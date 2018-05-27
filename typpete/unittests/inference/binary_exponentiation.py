"""Binary exponentiation"""
from typing import TypeVar

AnyNum = TypeVar("Num", bool, int, float, complex)


def exp(a: AnyNum, b: int) -> AnyNum:
    res = 1
    while b > 0:
        if b & 1 != 0:
            res = res * a
        a = a * a
        b >>= 1
    return res


def f(x):
    a = exp(x, 2)
    b = exp(2.0, x)

    return a * b


x = exp(1, 2)
y = exp(2.0, 3)


# f := Callable[[int], float]
# x := int
# y := float
