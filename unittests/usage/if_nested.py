x = int(input())
y = int(input())
a = int(input())
b = int(input())
# RESULT: a -> O, b -> N, x -> U, y -> N
if not 3 > x:  # x decision
    # inside nested if only b is modified!
    if 2 > y:  # y decision
        b = 10
    else:
        b = 20
    a = 10
else:
    # inside nested if only b is modified!
    if 2 > y:  # y decision
        b = 10
    else:
        b = 20
    a = 20
print(a)
