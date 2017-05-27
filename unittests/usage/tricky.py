x = False
# RESULT: x -> U, y -> O
y = True
if x:
    x = x and y
    y = False
x = x
if x:
     x = x and y
     y = False
print(y)
