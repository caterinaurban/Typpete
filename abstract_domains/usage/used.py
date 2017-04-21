from abstract_domains.lattice import Lattice
from enum import Flag


class Used(Flag):
    """Used state of a program variable."""
    # do not change values blindly, they are used for easy implementation with bitwise operators
    U = 3
    UU = 2
    UN = 1
    N = 0


U = Used.U
UU = Used.UU
UN = Used.UN
N = Used.N


class UsedLattice(Lattice):
    """Used variable analysis core abstract domain representation."""

    _DESCEND = {
        U: UU,
        UU: UU,
        UN: N,
        N: N
    }

    _COMBINE = {
        (N, N): N,
        (N, UU): UU,
        (N, UN): UN,
        (N, U): U,

        (UU, N): UU,
        (UU, UU): UU,
        (UU, UN): UN,
        (UU, U): U,

        (UN, N): UN,
        (UN, UU): UU,
        (UN, UN): UN,
        (UN, U): U,

        (U, N): U,
        (U, UU): U,
        (U, UN): UN,
        (U, U): U,
    }

    def __init__(self, used: Used = N):
        """Used variable analysis core abstract domain representation.
        
        :param used: initial lattice element
        """
        super().__init__()
        self._used = used

    @property
    def used(self):
        return self._used

    def __repr__(self):
        return self.used.name

    def default(self):
        self._used = N
        return self

    def bottom(self):
        self._used = N
        return self

    def top(self):
        self._used = U
        return self

    def is_bottom(self) -> 'bool':
        return self.used == N

    def is_top(self) -> 'bool':
        return self.used == U

    def _less_equal(self, other: 'UsedLattice') -> bool:
        if self.used == other.used or self.used == N:
            return True
        elif (self.used == UU and other.used == UN) or (
                        self.used == UN and other.used == UU):
            return False
        else:
            return other.used == UsedLattice.U

    def _meet(self, other: 'UsedLattice'):
        self.used &= other.used
        return self

    def _join(self, other: 'UsedLattice') -> 'UsedLattice':
        self.used |= other.used
        return self

    def _widening(self, other: 'UsedLattice'):
        return self._join(other)

    def descend(self) -> 'UsedLattice':
        self.used = UsedLattice._DESCEND[self.used]
        return self

    def combine(self, other: 'UsedLattice') -> 'UsedLattice':
        self.used = UsedLattice._COMBINE[(self.used, other.used)]
        return self
