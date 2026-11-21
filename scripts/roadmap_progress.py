#!/usr/bin/env python3
"""Считает прогресс по недельным чек-листам и обновляет dashboard в README.

По умолчанию скрипт пересчитывает `roadmap/README.md` между маркерами
`<!-- progress:start -->` и `<!-- progress:end -->`.

Запуск:
    python3 scripts/roadmap_progress.py
    python3 scripts/roadmap_progress.py --check
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "roadmap" / "data" / "roadmap.json"
WEEKS_DIR = ROOT / "roadmap" / "weeks"
README = ROOT / "roadmap" / "README.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_roadmap import week_topic_counts  # noqa: E402

STAGES: list[tuple[int, int, str]] = [
    (1, 6, "База"),
    (7, 11, "Classic ML"),
    (12, 17, "Deep Learning и Python Advanced"),
    (18, 35, "NLP, LLM, RAG, агенты"),
    (36, 36, "Выход на рынок"),
    (37, 45, "Дополнительно"),
]

CHECKBOX = re.compile(r"^- \[([ xX])\] (.+)$")
OPTIONAL_WORDS = {"дополнительно", "ресерч", "можно позже"}


def is_core(text: str) -> bool:
    """Тема ядерная, если в её бейдже нет optional-слов."""
    if " · " not in text:
        return True
    suffix = text.rsplit(" · ", 1)[1]
    parts = {part.strip() for part in suffix.split(",")}
    return not (parts & OPTIONAL_WORDS)


class WeekStats:
    def __init__(self, number: int, hours: int) -> None:
        self.number = number
        self.hours = hours
        self.topics = 0
        self.topics_done = 0
        self.core = 0
        self.core_done = 0
        self.summary = 0
        self.summary_done = 0

    @property
    def closed(self) -> bool:
        return self.summary > 0 and self.summary_done == self.summary

    @property
    def hours_done(self) -> float:
        if self.closed:
            return float(self.hours)
        if self.topics:
            return self.hours * self.topics_done / self.topics
        return 0.0


def parse_week(path: Path, number: int, hours: int) -> WeekStats:
    stats = WeekStats(number, hours)
    if not path.exists():
        return stats

    section = "topics"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Практика недели"):
            section = "practice"
            continue
        if line.startswith("## Мок-собес"):
            section = "practice"
            continue
        if line.startswith("## Сессия с тьютором"):
            section = "practice"
            continue
        if line.startswith("## Итог недели"):
            section = "summary"
            continue

        match = CHECKBOX.match(line)
        if not match:
            continue
        done = match.group(1).lower() == "x"
        text = match.group(2).strip()

        if section == "topics":
            stats.topics += 1
            stats.topics_done += int(done)
            if is_core(text):
                stats.core += 1
                stats.core_done += int(done)
        elif section == "summary":
            stats.summary += 1
            stats.summary_done += int(done)

    return stats


def load_weeks(data: dict) -> list[WeekStats]:
    result: list[WeekStats] = []
    for week in data["weeks"]:
        number = week["w"]
        path = WEEKS_DIR / f"week-{number:02d}.md"
        result.append(parse_week(path, number, week["h"]))
    return result


def aggregate(stats: list[WeekStats], start: int, end: int) -> dict[str, float]:
    selected = [week for week in stats if start <= week.number <= end]
    return {
        "weeks": len(selected),
        "closed": sum(week.closed for week in selected),
        "topics": sum(week.topics for week in selected),
        "topics_done": sum(week.topics_done for week in selected),
        "core": sum(week.core for week in selected),
        "core_done": sum(week.core_done for week in selected),
        "hours": sum(week.hours for week in selected),
        "hours_done": sum(week.hours_done for week in selected),
    }


def fmt(value: float) -> str:
    return f"{value:.0f}" if abs(value - round(value)) < 0.05 else f"{value:.1f}"


def percent(done: float, total: float) -> str:
    if not total:
        return "—"
    return f"{100 * done / total:.0f}%"


def dashboard(stats: list[WeekStats]) -> str:
    lines = [
        "| Этап | Недели | Темы | Ядро | Часы |",
        "|---|---|---|---|---|",
    ]
    for start, end, name in STAGES:
        row = aggregate(stats, start, end)
        lines.append(
            f"| {name} | {row['closed']}/{row['weeks']} | "
            f"{row['topics_done']}/{row['topics']} | "
            f"{row['core_done']}/{row['core']} | "
            f"{fmt(row['hours_done'])}/{fmt(row['hours'])} |"
        )

    total = aggregate(stats, 1, 45)
    lines += [
        f"| **Итого** | **{total['closed']}/{total['weeks']}** | "
        f"**{total['topics_done']}/{total['topics']}** | "
        f"**{total['core_done']}/{total['core']}** | "
        f"**{fmt(total['hours_done'])}/{fmt(total['hours'])}** |",
        "",
        f"Темы: {percent(total['topics_done'], total['topics'])} · "
        f"ядро: {percent(total['core_done'], total['core'])} · "
        f"часы: {percent(total['hours_done'], total['hours'])}.",
        "",
        "`[x]` ставится только после проверки тьютором на уровне ≥3. "
        "646 часов — обязательная часть, ещё 140 — дополнительные недели 37–45.",
    ]
    return "\n".join(lines)


def update_readme(block: str) -> bool:
    if not README.exists():
        print(f"Нет файла {README}", file=sys.stderr)
        return False
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(
        r"<!-- progress:start -->.*?<!-- progress:end -->",
        re.DOTALL,
    )
    if not pattern.search(text):
        print("В roadmap/README.md нет маркеров progress:start/end", file=sys.stderr)
        return False
    replacement = f"<!-- progress:start -->\n{block}\n<!-- progress:end -->"
    README.write_text(pattern.sub(replacement, text), encoding="utf-8")
    return True


def check(stats: list[WeekStats], data: dict) -> int:
    errors: list[str] = []
    for week in data["weeks"]:
        number = week["w"]
        expected_total, expected_core = week_topic_counts(data, number)
        actual = next(item for item in stats if item.number == number)
        if (actual.topics, actual.core) != (expected_total, expected_core):
            errors.append(
                f"неделя {number:02d}: в файле {actual.topics}/{actual.core} тем "
                f"(ядро/всего), в данных {expected_total}/{expected_core}"
            )

    total_topics = sum(item.topics for item in stats)
    total_core = sum(item.core for item in stats)
    expected_topics = sum(
        len(block["items"])
        for track in data["tracks"].values()
        for block in track["blocks"]
    )
    expected_core = sum(
        1
        for track in data["tracks"].values()
        for block in track["blocks"]
        for item in block["items"]
        if not set((item.get("b") or "").split()) & {"additional", "research", "later"}
    )
    if total_topics != expected_topics:
        errors.append(f"всего тем: {total_topics}, ожидалось {expected_topics}")
    if total_core != expected_core:
        errors.append(f"всего ядерных тем: {total_core}, ожидалось {expected_core}")

    if errors:
        for error in errors:
            print(f"ОШИБКА: {error}", file=sys.stderr)
        return 1
    print(f"Проверка пройдена: {total_topics} тем, из них {total_core} ядерных.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="проверить файлы, ничего не записывать")
    args = parser.parse_args()

    data = json.loads(DATA.read_text(encoding="utf-8"))
    stats = load_weeks(data)

    if args.check:
        return check(stats, data)

    block = dashboard(stats)
    total = aggregate(stats, 1, 45)
    print(
        f"Темы: {total['topics_done']}/{total['topics']} "
        f"({percent(total['topics_done'], total['topics'])}), "
        f"ядро: {total['core_done']}/{total['core']} "
        f"({percent(total['core_done'], total['core'])}), "
        f"часы: {fmt(total['hours_done'])}/{fmt(total['hours'])}."
    )
    print(f"Закрыто недель: {total['closed']}/{total['weeks']}.")
    if update_readme(block):
        print(f"Dashboard обновлён: {README.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
