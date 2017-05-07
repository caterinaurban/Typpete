# RESULT: x -> N, y -> O, z -> O
x = y = z = 2 + 1
# RESULT: x -> N, y -> U, z -> O
if y < 3:
    z = y
else:
    z = y * y
print(z)
