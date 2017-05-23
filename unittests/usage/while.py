n = 10
x = 18
i = 0
# RESULT: i -> U, n -> U, x -> O
while i < n:
    x = i / 2  # BUG: should be x = x / 2
    i = i + 1
else:
    x = -1
print(x)
