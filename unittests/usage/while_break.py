n = int(input())
x = int(input())
i = 0
while i < n:
    x = x / 2
    if x < 1:
        if i > 3:
            x = 0
            break
        continue
    else:
        x = 1
    print(x)
    i = i + 1
else:
    x = 3

while i < n:
    break
print(n)
