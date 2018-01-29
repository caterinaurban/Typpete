x = []

y = x.count("b")
x.append("a")
x.extend(["c", "d"])
z = x.index("e")
x.insert(1, "f")
a = x.pop()
x.remove("st")
x.reverse()
x.sort()
a[y:z]

class A:
    def append(self, x):
        pass

i = A()
i.append(1)

# x := List[str]
# a := str
# y := int
# z := int
# A := Type[A]
# i := A
