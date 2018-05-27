class A:
    def f(self):
        return 1


class B:
    def g(self):
        return "str"


class C(A, B):
    pass


def a(x):
    return x.f()


def b(x):
    return x.g()


def c(x):
    return x.g() + str(x.f())


a(A())
a(C())

b(B())
b(C())

c(C())


# A := Type[A]
# B := Type[B]
# C := Type[C]
# a := Callable[[A], int]
# b := Callable[[B], str]
# c := Callable[[C], str]
