#ifndef GCD_HPP_
#define GCD_HPP_

template <class T>
T Gcd(T x, T y) {
  while (y != 0) {
    T rest = x % y;
    x = y;
    y = rest;
  }
  return x;
}

#endif
