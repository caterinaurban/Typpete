x = int(input())
a = 0

if x < 3:
    a = x  # this implicitly upper bounds a, since x < 3 when assignment happens

# surprisingly octagon domain does not detect that a < 3 in any case :(
# this is because the closure does not infer a≤2 from x≤2, x-a≤0, -x+a≤0

# RESULT: TOP

print(a)
