class A:
    @staticmethod
    def f():
        return 1

    def g(self):
        return A.f()

x = A.f()
y = A().g()

# A := Type[A]
# f := Callable[[], int]
# g := Callable[[A], int]

# x := int
# y := int
