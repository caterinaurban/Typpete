class A:
    def __init__(self, x=1):
        pass


def f(A):
    x = A()
    y = A(1)

f(A)

x = A()
y = A(1)

# A := Type[A]
# f := Callable[[Type[A]], None]
# x := A
# y := A
