def f(x, y):
    return x(y)


def a(x: int):
    return x


def b(x: str):
    return x


f(a, 1)
f(b, "str")

# unsat

"""This program should type correctly after implemeting interfaces

The type of should be:
Callable[[Callable[object, object]], object]
"""