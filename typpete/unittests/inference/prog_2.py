n = int(input())
w = int(input())
arr = [int(x) for x in input().split(" ")]
arr2 = [(x + 1) // 2 for x in arr]
s = sum(arr2)
if w < s:
    print(-1)
else:
    w -= s
    while w > 0:
        m = max(arr)
        v = arr.index(m)
        while arr2[v] < arr[v] and w > 0:
            arr2[v] += 1
            w -= 1
        arr[v] = -1
    for i in range(n):
        print(arr2[i])


# arr := List[int]
# arr2 := List[int]
# i := int
# m := int
# n := int
# s := int
# v := int
# w := int

