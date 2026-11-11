class Solution:
    def getconcatenation(self, nums: list[int]) -> list[int]:
        n = len(nums)
        ans = nums.copy()
        i = 0
        while i < n:
            ans.append(nums[i])
            i += 1
        return ans

