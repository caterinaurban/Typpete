from typing import Tuple
def tosomething(mmmm : Tuple[bool, int], eeee) -> Tuple[float, ...]:
# def tosomething(mmmm, eeee: int) -> float:

    return mmmm



a = 1 + 2 / 3
a += 0
b = -a
c = [1.2, 2.0, b]
d = [[1.1, 2.5], c]
e = {(i, i * 2) for j in d for i in j}
f = 2 & 3
g = d[f]
h = (g, 2.0, a)
i, j, (k, (l, m)) = {1: 2.0}, True, ((1, 2), (f, e))
n = a if True else "string"
o = (1 is 2) + 1
p = i[o]

asdasd = tosomething((j,l), 45345)

asdasd = (1.2, 3)

# a := float
# b := float
# c := List[float]
# d := List[List[float]]
# e := Set[Tuple[float, float]]
# f := int
# g := List[float]
# h := Tuple[List[float], float, float]
# i := Dict[int, float]
# j := bool
# k := Tuple[int, int]
# l := int
# m := Set[Tuple[float, float]]
# n := object
# o := int
# p := float