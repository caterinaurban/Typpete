x1 = input()  # x1 unused
x2 = input()
x3 = input()

# RESULT: asc -> O, temp -> O, x1 -> N, x2 -> U, x3 -> U

asc = True
if x1 <= x2:
    temp = False
else:
    temp = True

# BUG, missing update on asc

if x2 <= x3:
    temp = False
else:
    temp = True

asc = asc and temp

print(asc)
