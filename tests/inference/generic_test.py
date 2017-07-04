



def generic_tolist(a):
    b = a + 1
    return [a]

u = generic_tolist(1.2)
u[0] = 2.4
v = generic_tolist(True)
v2 = v[v[0]]
# v3 = v[0] + 2