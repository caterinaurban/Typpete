# type_params {'concatenate': [1,2]}
from typing import TypeVar, Generic

TC = TypeVar("TC")

class Concatenator(Generic[TC]):
    def __init__(self, a):
        self.a = a


    def concatenate(self, separator, from_, to):
        self.a = separator
        to.append(separator)
        for f in from_:
            to.append(f)


class Z:
    def foo(self):
        pass

class Y(Z):
    def bar(self):
        pass

class X(Y):
    def baz(self):
        pass

class W(X):
    def omg(self):
        pass


concatenator = Concatenator(Y())
concatenator.a.bar()

wlst = [W()]
wlst[0].omg()
xlst = [X()]
xlst[0].baz()
concatenator.concatenate(X(), wlst, xlst)

class ZP:
    def foo(self):
        pass

class YP(ZP):
    def bar(self):
        pass

class XP(YP):
    def baz(self):
        pass

class WP(XP):
    def omg(self):
        pass

concatenatorP = Concatenator(YP())
concatenatorP.a.bar()

wlstP = [WP()]
wlstP[0].omg()
xlstP = [XP()]
xlstP[0].baz()
concatenatorP.concatenate(XP(), wlstP, xlstP)