x = dict()
x[2.0] = "string"
y = x.copy()
y.clear()
a = x.get(2.0)
d = x.pop(2.0)
e = x.popitem()
x.update(y)

f = a[0] + d[0]
g = e[0]

# x := Dict[float, str]
# y := Dict[float, str]
# a := str
# d := str
# e := Tuple[float, str]
