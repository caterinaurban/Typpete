n = 4
x = 22
i = 0
while i < n:
    x = x / 2
    if x < 1:
        if i > 3:
            x = 0
            continue
        break
    i = i + 1
else:
    x = 3

while i < n:
    break
print(x)
