# LeetCode 1929. Concatenation of Array
# Условие: вернуть массив длины 2n, в котором nums записан два раза подряд.
# Время: O(N) (цикл на n шагов + копирование n элементов).
# Память: O(N) (ans хранит 2n элементов).

class Solution:
    def getconcatenation(self, nums: list[int]) -> list[int]:
        n = len(nums)
        ans = nums.copy()
        i = 0
        while i < n:
            ans.append(nums[i])
            i += 1
        return ans


