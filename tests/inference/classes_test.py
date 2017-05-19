class A:
    def f(self):
        return 1


class B:
    def f(self):
        return "string"


def f(a):
    return a().f()

x = f(B)
y = x + "st"
# y = x + 1  # --> Invalid

# ------------------------------


class C:
    x = 1

c = C()
c.x += True
y = c.x
d = [1, 2, 3][y]
