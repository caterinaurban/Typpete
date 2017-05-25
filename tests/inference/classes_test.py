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


# A := Type[A]
# B := Type[B]
# C := Type[C]
# D := Type[D]
# E := Type[E]

# x := str
# c := C
# e := E
# fab := Callable[[Type[B]], str]
