class Lattice:
    def bottom(self): pass
    
    def top(self): pass
    
    def is_bottom(self): pass

    def is_top(self): pass

    def _less_equal(self, other): pass
    
    def less_equal(self, other):
        if self.is_bottom() or other.is_top():
            return True
        elif other.is_bottom() or self.is_top():
            return False
        else:
            return self._less_equal(other)

    def _join(self, other): pass

    def join(self, other):
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        elif other.is_bottom() or self.is_top():
            return self
        else:
            return self._join(other)

    def _meet(self, other): pass

    def meet(self, other):
        if self.is_top() or other.is_bottom():
            return self.replace(other)
        elif other.is_top() or self.is_bottom():
            return self
        else:
            return self._meet(other)

    def _widening(self, other): pass

    def widening(self, other):
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        else:
            return self._widening(other)

    def replace(self, other):
        return self


class BoundedLattice(Lattice):
    def __init__(self):
        self.kind = 2

    def bottom(self):
        self.kind = 1
        return self

    def top(self):
        self.kind = 3
        return self

    def is_bottom(self):
        return self.kind == 1

    def is_top(self):
        return self.kind == 3


# Lattice := Type[Lattice]
# BoundedLattice := Type[BoundedLattice]
