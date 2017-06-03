x = True
y = True
while x:
    if y:
        b = input()
        y = False
    else:
        y = b
        x = False
print(y)
