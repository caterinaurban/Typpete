class A:
    def __init__(self):
        self.x = 1
        self.y = 2.0

    def __call__(self, z):
        return z + [self.x + self.y]

x = A()
y = x([])

# A := Type[A]
# __call__ := Callable[[A, List[float]], List[float]]
# x := A
# y := List[float]

