#!/usr/bin/env python3
"""Собирает недельные чек-листы роадмапа из исходного HTML.

Источник: roadmap/source/roadmap-ml-2026.html (внутри лежит JSON `const D = ...`).
Результат: roadmap/data/roadmap.json и roadmap/weeks/week-NN.md.

Скрипт можно запускать повторно: уже отмеченные `[x]` темы сохраняются,
если текст темы не менялся.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "roadmap" / "source" / "roadmap-ml-2026.html"
DATA = ROOT / "roadmap" / "data" / "roadmap.json"
WEEKS_DIR = ROOT / "roadmap" / "weeks"

# Порядок групп и треков повторяет GROUPS из исходного HTML.
GROUPS: list[tuple[str, list[str]]] = [
    ("Математика", ["math"]),
    ("Python", ["python"]),
    ("Classic ML и Deep Learning", ["classic_ml", "dl", "models-dl"]),
    (
        "NLP и LLM",
        [
            "nlp-base",
            "nlp-advanced",
            "models-nlp",
            "nlp-optimization",
            "nlp-rag",
            "nlp-agents",
        ],
    ),
    (
        "Вспомогательные разделы",
        ["github", "linux", "mlops-docker", "architecture", "career"],
    ),
    (
        "Дополнительные разделы",
        [
            "recsys",
            "timeseries",
            "cv",
            "cv-dl",
            "models-cv",
            "mlops-k8s",
            "mlops-kafka",
            "mlops-cloud",
            "mlops-db",
            "mlops-mlflow",
            "mlops-tensorboard",
            "mlops-wandb",
            "mlops-clearml",
            "mlops-prometheus",
            "mlops-grafana",
        ],
    ),
]

BADGE_WORDS = {
    "required": "обязательно",
    "additional": "дополнительно",
    "research": "ресерч",
    "later": "можно позже",
}

PHASE_RU = {
    "Foundation": "База",
    "Classic ML": "Classic ML",
    "Deep Learning": "Deep Learning",
    "Python Advanced": "Python Advanced",
    "NLP": "NLP и LLM",
    "NLP + Tools": "NLP и LLM",
    "NLP Advanced": "NLP и LLM",
    "NLP Projects": "NLP и LLM",
    "Job Search": "Выход на рынок",
    "Additional": "Дополнительно",
    "Additional MLOps": "Дополнительно",
    "Additional CV": "Дополнительно",
}

# Блок ML System Design в источнике не привязан к неделе.
# Проходим его вместе с неделей 31 («MLSD по проектам из резюме»).
EXTRA_BLOCK_WEEK = {"architecture": 31}

PRACTICE: dict[int, str] = {
    1: "Диагностика тьютора: пропустить уже известные темы Python/Git. Конспект по математике, 5 задач на Python.",
    2: "Конспект по математике; 5–7 задач на Python; первые команды Git на практике.",
    3: "Конспект по теорверу; практика Linux (файлы, пути, поиск); задачи на Python.",
    4: "Закрыть математику и Python Base; ноутбук с numpy/pandas/matplotlib.",
    5: "Решить 10–15 задач LeetCode по подходам недели, записать сложность в `algorithms/README.md`.",
    6: "Мок-собес Python Foundation: 60–90 минут без подсказок, разбор ошибок.",
    7: "Ноутбук: метрики бинарной и многоклассовой классификации на табличных данных.",
    8: "Ноутбук: train/valid/test, кросс-валидация, preprocessing, дерево решений.",
    9: "Ноутбук: ансамбли (bagging/boosting) и кластеризация.",
    10: "Проект №1: табличный Kaggle-датасет — EDA → модель → метрики → README в `projects/`.",
    11: "Мок-собес Classic ML: 60–90 минут, разбор ошибок и пробелов.",
    12: "Ноутбук: функция потерь, backprop, оптимизаторы; сравнить SGD и Adam.",
    13: "Ноутбук: полносвязная сеть на PyTorch; параллельно Python Advanced.",
    14: "Ноутбук: внимание и мини-трансформер; обзор генеративных моделей.",
    15: "Мок-собес Deep Learning: 60–90 минут, разбор ошибок.",
    16: "Практика: GIL, threading/multiprocessing, async; замерить время выполнения.",
    17: "Проект №2: PyTorch-проект (изображения или текст) с README в `projects/`.",
    18: "Ноутбук: предобработка текста, BoW, TF-IDF, BM25.",
    19: "Ноутбук: Word2Vec/GloVe/FastText, оценка эмбеддингов.",
    20: "Ноутбук: n-граммная и нейронная языковая модель, токенизация BPE.",
    21: "Ноутбук: BERT/GPT на классификации текста; GitHub Actions для репозитория.",
    22: "Docker: собрать образ для ML-inference, запустить контейнер, описать в README.",
    23: "Конспект: attention-схемы, RoPE, MoE, обзор архитектур LLM.",
    24: "Конспект: дистилляция, latency/RPS, метрики качества генерации.",
    25: "Конспект: квантизация (линейная, LLM.Int8, GPTQ, GGUF, AWQ).",
    26: "Конспект: speculative decoding, batching, KV-cache, LoRA/QLoRA.",
    27: "Мок-собес NLP Base / Advanced / Optimization: 60–90 минут.",
    28: "Проект №3: RAG-сервис — загрузка документов, чанки, векторный поиск, ответы.",
    29: "Мок-собес RAG: 60–90 минут, разбор ошибок.",
    30: "Резюме и легенда: собрать черновик, вычитать, приложить ссылки на проекты.",
    31: "MLSD по проектам из резюме: 2–3 истории по шаблону, записать в `projects/`.",
    32: "Мок-собес: резюме, легенда и MLSD; разбор обратной связи.",
    33: "Ноутбук: tool calling, ReAct, structured output; сравнить с RAG.",
    34: "Проект №4: LLM-агент (инструменты, память, observability) с README.",
    35: "Мок-собес Agents: 60–90 минут, разбор ошибок.",
    36: "Выход на рынок: профили HH/LinkedIn, банк вопросов, план откликов.",
    37: "Мини-проект: baseline recommender на открытом датасете (опционально).",
    38: "Мини-проект: прогноз временного ряда, честная валидация (опционально).",
    39: "Практика: локальный Kubernetes-кластер и Kafka (опционально).",
    40: "Практика: cloud + база данных для ML-сервиса (опционально).",
    41: "Практика: трекинг экспериментов в MLflow/W&B (опционально).",
    42: "Практика: метрики и дашборды Prometheus/Grafana (опционально).",
    43: "Ноутбук: классическое CV — фильтры, границы, гомография (опционально).",
    44: "Ноутбук: детекция и сегментация, mAP/IoU (опционально).",
    45: "Мини-проект: CV/DL-пайплайн или мультимодальная модель (опционально).",
}

STAGE_GOALS = {
    "База": "Заложить математику и Python, закрыть Git/Linux и выйти на первый мок-собес.",
    "Classic ML": "Научиться честно валидировать табличные модели и защитить первый проект.",
    "Deep Learning": "Понять обучение нейросетей, внимание и трансформеры, собрать PyTorch-проект.",
    "Python Advanced": "Довести инженерные навыки Python до уровня продакшена.",
    "NLP и LLM": "Пройти путь от текста в числах до LLM, RAG и агентов, собрать портфолио.",
    "Резюме и MLSD": "Упаковать проекты в резюме и научиться рассказывать ML System Design.",
    "Агенты": "Собрать LLM-агента с инструментами, памятью и observability.",
    "Выход на рынок": "Упаковать опыт в резюме и выйти на отборы.",
    "Дополнительно": "Добрать специализацию и MLOps после первого оффера.",
}


def week_phase(number: int, raw_phase: str) -> str:
    """Уточняет фазу по неделе: в источнике 30–35 помечены как NLP Projects."""
    if 30 <= number <= 32:
        return "Резюме и MLSD"
    if 33 <= number <= 35:
        return "Агенты"
    return PHASE_RU.get(raw_phase, raw_phase)


def week_goal(number: int, phase: str) -> str:
    if number <= 6:
        return STAGE_GOALS["База"]
    if number <= 11:
        return STAGE_GOALS["Classic ML"]
    if number <= 15:
        return STAGE_GOALS["Deep Learning"]
    if number <= 17:
        return STAGE_GOALS["Python Advanced"]
    if number <= 29:
        return STAGE_GOALS["NLP и LLM"]
    if number <= 32:
        return STAGE_GOALS["Резюме и MLSD"]
    if number <= 35:
        return STAGE_GOALS["Агенты"]
    if number == 36:
        return STAGE_GOALS["Выход на рынок"]
    return STAGE_GOALS["Дополнительно"]


def extract_data(html: str) -> dict:
    marker = "const D = "
    start = html.index(marker) + len(marker)
    depth = 0
    in_string = False
    escaped = False
    for pos in range(start, len(html)):
        char = html[pos]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(html[start : pos + 1])
    raise ValueError("Не найден JSON-объект const D в исходном HTML")


def badge_suffix(raw: str | None) -> str:
    if not raw:
        return ""
    words = [BADGE_WORDS[word] for word in raw.split() if word in BADGE_WORDS]
    return " · " + ", ".join(words) if words else ""


def block_title(block: dict) -> str:
    section = block.get("s") or block.get("name")
    if not section:
        topics = [item["t"] for item in block["items"][:3]]
        section = " · ".join(topics)
        if len(block["items"]) > 3:
            section += " …"
    return f"Блок {block['n']}. {section}"


def week_blocks(data: dict, week: int) -> list[tuple[str, str, dict]]:
    """Возвращает (группа, название трека, блок) в порядке прохождения."""
    result: list[tuple[str, str, dict]] = []
    for group, tracks in GROUPS:
        for track_key in tracks:
            track = data["tracks"].get(track_key)
            if not track:
                continue
            for block in track["blocks"]:
                in_week = week in block.get("w", [])
                extra = EXTRA_BLOCK_WEEK.get(track_key) == week
                if in_week or extra:
                    result.append((group, track["title"], block))
    return result


def week_topic_counts(data: dict, week: int) -> tuple[int, int]:
    total = core = 0
    for _, _, block in week_blocks(data, week):
        for item in block["items"]:
            total += 1
            words = set((item.get("b") or "").split())
            if not words & {"additional", "research", "later"}:
                core += 1
    return total, core


def load_previous_states(path: Path) -> dict[str, bool]:
    """Читает `[x]` из старого файла: текст темы -> состояние."""
    states: dict[str, bool] = {}
    if not path.exists():
        return states
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^- \[([ xX])\] (.+)$", line)
        if match:
            text = match.group(2).strip()
            states[text] = match.group(1).lower() == "x"
    return states


def render_week(data: dict, week: dict, previous: dict[str, bool]) -> str:
    number = week["w"]
    title = week["title"]
    phase = week_phase(number, week["phase"])
    hours = week["h"]
    mock = week.get("mock")
    mock = re.sub(r"^W\d+:\s*", "", mock) if mock else None
    total, core = week_topic_counts(data, number)
    optional = number >= 37
    goal = week_goal(number, phase)

    lines: list[str] = [
        f"# Неделя {number:02d} — {title}",
        "",
        f"**Фаза:** {phase} · **Часы:** {hours} · "
        f"**Мок:** {'да — ' + mock if mock else 'нет'} · "
        f"**Ядро:** {core} из {total} тем",
        "",
    ]

    if optional:
        lines += [
            "> Дополнительная неделя. Можно отложить до первого оффера.",
            "",
        ]

    lines += [f"Цель: {goal}", ""]

    blocks = week_blocks(data, number)
    if not blocks:
        lines += [
            "## Новых тем нет",
            "",
            "Эта неделя отведена под повторение и мок-собес. Новые темы не добавляются.",
            "",
        ]
    else:
        current_group = None
        current_track = None
        for group, track_title, block in blocks:
            if group != current_group:
                lines += [f"## {group}", ""]
                current_group = group
                current_track = None
            if track_title != current_track and track_title != group:
                lines += [f"### {track_title}", ""]
                current_track = track_title
            lines += [f"#### {block_title(block)}", ""]
            for item in block["items"]:
                suffix = badge_suffix(item.get("b"))
                text = f"{item['t']}{suffix}"
                mark = "x" if previous.get(text) else " "
                lines.append(f"- [{mark}] {text}")
            lines.append("")
            if track_title == "MLSD" and number == EXTRA_BLOCK_WEEK["architecture"]:
                lines += [
                    "> В источнике у этого блока нет недели; проходим его вместе с MLSD по проектам.",
                    "",
                ]

    practice = PRACTICE.get(number, "Конспект в `ml-learning/`; 3–5 практических задач по темам недели.")
    lines += ["## Практика недели", ""]
    if blocks:
        lines += [
            f"- [ ] {practice}",
            "- [ ] Конспект записан в [`ml-learning/`](../../ml-learning/README.md)",
            "",
        ]
    else:
        lines += [
            "- [ ] Повторить конспекты прошлых недель",
            "- [ ] Закрыть долги по практическим заданиям",
            "",
        ]

    if mock:
        lines += [
            "## Мок-собес",
            "",
            "- [ ] Собрать 10–15 вопросов по пройденному материалу",
            "- [ ] Пройти мок без подсказок (60–90 минут)",
            "- [ ] Разобрать ошибки и обновить [`../progress.md`](../progress.md)",
            "",
        ]

    # Черновик поднавыков: первые ядерные темы недели.
    core_topics: list[str] = []
    for _, _, block in blocks:
        for item in block["items"]:
            if not item.get("b"):
                core_topics.append(item["t"])
    draft = ", ".join(core_topics[:5]) if core_topics else "повторение пройденного"

    lines += [
        "## Сессия с тьютором",
        "",
        f"Черновик поднавыков: {draft}.",
        "",
        "- [ ] Диагностика: 3–5 вопросов по темам недели",
        "- [ ] Выбрать 4–8 поднавыков и занести в [`../progress.md`](../progress.md)",
        "- [ ] Довести активные поднавыки до 3/5, затем до 4/5",
        "- [ ] Обновить `resume from:` в `progress.md`",
        "",
        "```text",
        f"topic: Неделя {number:02d} — {title}",
        "levels: ...",
        "covered: ...",
        "misconceptions: ...",
        "open: ...",
        "next: ...",
        "```",
        "",
        "## Итог недели",
        "",
        "- [ ] Ядро недели закрыто (уровень ≥3 по каждой теме)",
        "- [ ] Практика выполнена",
        "- [ ] Конспект и `resume from:` обновлены",
        "",
    ]

    prev_link = (
        f"[← Неделя {number - 1:02d}](week-{number - 1:02d}.md)"
        if number > 1
        else "[← К роадмапу](../README.md)"
    )
    next_link = (
        f"[Неделя {number + 1:02d} →](week-{number + 1:02d}.md)"
        if number < 45
        else "[К роадмапу →](../README.md)"
    )
    lines += [
        "---",
        "",
        f"{prev_link} · [Все недели](../README.md) · "
        f"[План](../PLAN.md) · [Прогресс](../progress.md) · {next_link}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="только проверить данные, не писать файлы")
    args = parser.parse_args()

    if not SOURCE.exists():
        print(f"Нет исходного файла: {SOURCE}", file=sys.stderr)
        return 1

    data = extract_data(SOURCE.read_text(encoding="utf-8"))
    total_topics = sum(
        len(block["items"])
        for track in data["tracks"].values()
        for block in track["blocks"]
    )
    required_hours = sum(week["h"] for week in data["weeks"] if week["w"] <= 36)
    all_hours = sum(week["h"] for week in data["weeks"])

    print(f"Недель: {len(data['weeks'])}, тем: {total_topics}")
    print(f"Часы: {required_hours} обязательных, {all_hours} всего")

    if args.check:
        expected = sum(week_topic_counts(data, week["w"])[0] for week in data["weeks"])
        if expected != total_topics:
            print(f"Ошибка: по неделям разложено {expected} тем, а в данных {total_topics}", file=sys.stderr)
            return 1
        print("Проверка пройдена: все темы разложены по неделям.")
        return 0

    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)

    for week in data["weeks"]:
        path = WEEKS_DIR / f"week-{week['w']:02d}.md"
        previous = load_previous_states(path)
        path.write_text(render_week(data, week, previous), encoding="utf-8")

    print(f"Записано: {DATA.relative_to(ROOT)} и {len(data['weeks'])} файлов в {WEEKS_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
