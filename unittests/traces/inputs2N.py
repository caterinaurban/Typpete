x = input()  # UNUSED
y = input()  # USED
if x:
    z = False
else:
    z = x
z = z or y
print(z)
