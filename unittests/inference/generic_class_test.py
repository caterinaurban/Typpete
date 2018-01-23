# class_type_params {'Cell': [0]}

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

my_a = c1.get()
my_b = c1.value
my_a = my_b

my_a.foo()

c2 = Cell(2)

a55 = c2.value + 23
mt = {1:"hi"}
mt2 = mt.copy()

a1 = c2.get() + 1