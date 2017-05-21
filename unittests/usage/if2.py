# RESULT: x -> N, y -> O, z -> O
x = y = z = 2 + 1
# RESULT: x -> N, y -> U, z -> U
if 1 < y < 3 or y < 5 and True:
    z = y
print(z)
