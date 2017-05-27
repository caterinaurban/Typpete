x = input()
y = True
while x:
    x = x and y
    y = False
print(y)
