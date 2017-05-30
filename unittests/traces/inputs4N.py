x = input()  # USED
y = input()  # UNUSED
if x:
    z = x
else:
    z = x
z = z or False
print(z)
