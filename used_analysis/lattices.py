from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier
from enum import Flag
from typing import List, Set


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

    class Internal(Lattice.Internal):
        def __init__(self, kind: Lattice.Kind):
            super().__init__(kind)
            self._used = U if Lattice.Kind == Lattice.Kind.Top else N

        @property
        def used(self) -> 'Used':
            return self._used

    def __init__(self, kind: Lattice.Kind = Lattice.Kind.Default):
        """Used variable analysis core abstract domain representation.
        
        :param kind: kind of lattice element
        """
        super().__init__(kind)
        self._internal = UsedLattice.Internal(kind)

    @property
    def internal(self):
        return self._internal

    @property
    def used(self):
        return self.internal.used

    def __str__(self):
        return self.used.name

    def _less_equal(self, other: 'UsedLattice') -> bool:
        if self.used == other.used or self.used == N:
            return True
        elif (self.used == UU and other.used == UN) or (
                        self.used == UN and other.used == UU):
            return None
        else:
            return other.used == UsedLattice.U

    def _meet(self, other: 'UsedLattice'):
        self.used &= other.used
        return self

    def _join(self, other: 'UsedLattice') -> 'UsedLattice':
        self.used |= other.used
        return self

    def descend(self):
        self.used = UsedLattice._DESCEND[self.used]
        return self

    def combine(self, other):
        self.used = UsedLattice._COMBINE[(self.used, other.used)]
        return self
