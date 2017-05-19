def f1(x, y):
    a = x + y
    b = x[0]
    c = x * 3
    return c * b


def f2(x):
    return [x]


def f3(x):
    return x


def f4(x, y):
    a = x["string"] + y
    b = y + 3
    return a | b


def f5(a, b, i):
    x = a * 3
    y = b["string"]
    z = a[i]
    return (x[0] + z) * (y + 3)


def f7(x):
    return x["string"]


a = f1([1, 2, 3], [])
b = f2(a[0])
c = f3(b)
d = f4({"": c[0]}, 2)
e = f5(a, {"": 2j}, 2)