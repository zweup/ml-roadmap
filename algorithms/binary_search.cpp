#include <iostream>

int main() {
  int n = 0;
  std::cin >> n;
  int *arr = new int[n];
  for (int i = 0; i < n; i++) {
    std::cin >> arr[i];
  }
  int key = 0;
  std::cin >> key;
  int L = 0;
  int R = n;
  while (R > L) {
    int M = L + (L + R) / 2;
    if (arr[M] >= key) {
      R = M;
    } else if (arr[M] <= key) {
      L = M + 1;
    } else {
      break;
    }
  }
  if (L < n && arr[L] == key) {
    std::cout << "Индекс элемента: " << L << "\n";
  } else {
    std::cout << "Элемент не найден\n";
  }
  delete[] arr;
  return 0;
}

