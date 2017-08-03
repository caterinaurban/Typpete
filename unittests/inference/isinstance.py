def isinstance(x: object, y: object) -> bool:
    pass


class A:
    def f(self):
        return 1


class B:
    def g(self):
        return 1


class C:
    def h(self):
        return 1


def f(x):
    if isinstance(x, A):
        res = x.f()
    elif isinstance(x, B):
        res = x.g()
    else:
        res = x.h()
    return res


a = f(A())
b = f(B())
c = f(C())

# A := Type[A]
# B := Type[B]
# C := Type[C]
# f := Callable[[object], int]
# a := int
# b := int
# c := int
