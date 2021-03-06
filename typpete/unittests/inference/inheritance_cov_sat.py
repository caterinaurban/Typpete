class A:
    def f(self, x, y, z=1):
        return x + y - z

    def g(self):
        return 1


class B(A):
    def f(self, x, y, z=1, m=3, n=5):
        return x + y - z

    def g(self, x=1):
        return 12


def f(cls):
    return cls.f(1, 2, 3)


f(A())
f(B())

# f := Callable[[A], int]
