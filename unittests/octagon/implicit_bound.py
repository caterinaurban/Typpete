x = int(input())
a = 0

if x < 3:
    a = x  # this implicitly upper bounds a, since x < 3 when assignment happens

pass  # without this, comment is interpreted to be inside if :(

# RESULT: a≤2, -x+a≤0

print(a)
