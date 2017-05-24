class A:
    def f(self):
        return 1


class B:
    def f(self):
        return "string"


def fab(a):
    return a().f()

x = fab(B)
y = x + "st"


class C:
    x = 1

c = C()
c.x += True
d = [1, 2, 3][c.x]


class D:
    def f(self):
        return 2


class E(D):
    pass


e = E()
f = e.f()


# A := type_type(class_A)
# B := type_type(class_B)
# C := type_type(class_C)
# D := type_type(class_D)
# E := type_type(class_E)

# x := str
# c := class_C
# e := class_E
# fab := func_1(type_type(class_B), str)
