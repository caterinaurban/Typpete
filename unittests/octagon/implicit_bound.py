x = int(input())
a = 0

if x < 3:
    a = x  # this implicitly upper bounds a, since x < 3 when assignment happens

print(a)
