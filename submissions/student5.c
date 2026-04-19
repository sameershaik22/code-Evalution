#include <stdio.h>

int main() {
    int n, target;
    scanf("%d %d", &n, &target);

    int arr[n];
    for(int i = 0; i < n; i++) scanf("%d", &arr[i]);

    for(int i = 0; i < n; i++) {
        for(int j = i + 1; j < n; j++) {
            if(arr[i] + arr[j] == target) {
                printf("%d %d", i + 1, j + 1);
                return 0;
            }
        }
    }
}