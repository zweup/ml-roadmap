#include <iostream>

int Nod(int x, int y) {
  if (x != 0 && y != 0) {
    if (x > y) {
      return Nod(x % y,y);
    }
    if (y > x) {
      return Nod(x, y % x);
    }
  }
  return x+y;
}

int main() {
  int x = 0;
  int y = 0;
  std::cin >> x >> y;
  std::cout << Nod(x,y);
}

