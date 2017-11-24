
class Cell:
    def __init__(self, val):
        self.value = val

    def get(self):
        return self.value

    def set(self, val):
        self.value = val


class A:
    def foo(self):
        return 12

c1 = Cell(A())

c1.get().foo()

c2 = Cell(2)

a1 = c2.get() + 1