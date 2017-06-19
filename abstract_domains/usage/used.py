from abstract_domains.lattice import BaseLattice
from enum import Flag


class Used(Flag):
    """Used state of a program variable."""
    # do not change values blindly, they are used for easy implementation with bitwise operators
    U = 3  # used in this scope or in a deeper nested scope
    S = 2  # used in an outer scope
    O = 1  # used in an outer scope and overridden in this scope
    N = 0  # not used


U = Used.U
S = Used.S
O = Used.O
N = Used.N


class UsedLattice(BaseLattice):
    """Used variable analysis core abstract domain representation."""

    DESCEND = {
        U: S,
        S: S,
        O: N,
        N: N
    }

    COMBINE = {
        (N, N): N,
        (N, S): S,
        (N, O): O,
        (N, U): U,

        (S, N): S,
        (S, S): S,
        (S, O): O,
        (S, U): U,

        (O, N): O,
        (O, S): S,
        (O, O): O,
        (O, U): U,

        (U, N): U,
        (U, S): U,
        (U, O): O,
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

    @used.setter
    def used(self, used: Used):
        self._used = used

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

    def is_bottom(self) -> bool:
        return self.used == N

    def is_top(self) -> bool:
        return self.used == U

    def _less_equal(self, other: 'UsedLattice') -> bool:
        if self.used == other.used or self.used == N:
            return True
        elif (self.used == S and other.used == O) or \
                (self.used == O and other.used == S):
            return False
        else:
            return other.used == U

    def _meet(self, other: 'UsedLattice'):
        self.used &= other.used
        return self

    def _join(self, other: 'UsedLattice') -> 'UsedLattice':
        self.used |= other.used
        return self

    def _widening(self, other: 'UsedLattice'):
        return self._join(other)

    def descend(self) -> 'UsedLattice':
        self._used = UsedLattice.DESCEND[self.used]
        return self

    def combine(self, other: 'UsedLattice') -> 'UsedLattice':
        self._used = UsedLattice.COMBINE[(self.used, other.used)]
        return self
