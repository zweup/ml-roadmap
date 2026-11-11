## 217. Contains Duplicate
## Given an integer array nums, return true if any value appears at least twice in the array, and return false if every element is distinct.
## T = O(n) но и M = O(n)

class Solution:
    def containsDuplicate(self, nums: list[int]) -> bool:
        hashset = set()
        for i in nums:
            if i in hashset:
                return True
            hashset.add(i)
        return False
