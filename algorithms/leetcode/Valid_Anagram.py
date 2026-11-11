## 242. Valid Anagram
## Given two strings s and t, return true if t is an anagram of s, and false otherwise. 
## T = O(n) но и M = O(n)
## но если надо задеть память О(1) то лучше прописать return sorted(s) == sorted(t)

class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        if len(s) != len(t):
            return False
        CounterS, CounterT = {}, {}
        for n in range(len(s)):
            CounterS[s[n]] = 1 + CounterS.get(s[n], 0)
            CounterT[t[n]] = 1 + CounterT.get(t[n], 0)
        for u in CounterS:
            if CounterS[u] != CounterT.get(u, 0):
                return False
        return True

