class A:
    def f(self):
        return B()

    def g(self):
        return self.f().g()


class B(A):
    def g(self):
        return "string"


x = A()
y = x.g()

# A := Type[A]
# B := Type[B]
# x := A
# y := str
