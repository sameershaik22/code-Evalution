n, target = map(int, input().split())
arr = list(map(int, input().split()))

mp = {}

for i in range(n):
    if target - arr[i] in mp:
        print(mp[target - arr[i]] + 1, i + 1)
        break
    mp[arr[i]] = i