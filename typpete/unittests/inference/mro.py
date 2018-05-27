class A:
    def who_am_i(self):
        return A()


class B(A):
    pass


class C(A):
    def who_am_i(self):
        return C()


class D(B, C):
    pass

d1 = D()
who = d1.who_am_i()

"""With the old MRO algorithm, the type of `who` would be Type[A], because
The naive DFS will reach A before C

With the C3 Linearization algorithm, C will appear first in the search context
so the type of `who` is Type[C]
"""

# A := Type[A]
# B := Type[B]
# C := Type[C]
# D := Type[D]
# d1 := D
# who := C
