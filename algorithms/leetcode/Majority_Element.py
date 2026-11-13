## 169. Majority Element Given an array nums of size n, return the majority element.
## The majority element is the element that appears more than ⌊n / 2⌋ times. You may assume that the majority element always exists in the array
## T = O(n) но и M = O(n)
## но если надо задеть память О(1) то лучше прописать return sorted(s) == sorted(t)
class Solution:
    def majorityElement(self, nums: list[int]) -> int:
        count = {}
        res, maxCount = 0, 0
        for n in nums:
            count[n] = 1 + count.get(n, 0)
            if count[n] > maxCount:
                res = n
                maxCount = count[n]
        return res

