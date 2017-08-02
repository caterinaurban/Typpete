x = bool(input())
# RESULT: x -> U, y -> O
y = bool(input())
if x:
    x = x and y
    y = False
if x:
    x = x and y
    y = False
print(y)
