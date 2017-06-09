from abstract_domains.lattice import BaseLattice

from abstract_domains.usage.used import U, S, O, N, UsedLattice, Used
from collections import OrderedDict
from math import inf


class UsedListStartLattice(BaseLattice):
    """Used list start analysis abstract domain representation.
    
    This uses the Used lattice as base and uses it to store the usage of the start of list, each Used element covers 
    a possibly empty sequence ``0:q``. Some additional consistency conditions hold for any element of this lattice 
    that was previously closed by ``closure()``. 
    """

    def __init__(self, s: float = 0, u: float = 0, o: float = 0):
        """Used list start analysis abstract domain representation.
        
        :param s: initial end of S-elements in list: should be a float in ``[0,1,2,..., inf]``
        :param u: initial end of U-elements in list: should be a float in ``[0,1,2,..., inf]``
        :param o: initial end of O-elements in list: should be a float in ``[0,1,2,..., inf]``
        """
        super().__init__()
        self._suo = OrderedDict([
            (S, s),
            (U, u),
            (O, o)
        ])

    @property
    def suo(self):
        return self._suo

    def used_at(self, index):
        """Finds usage at specified index.
        
        Does a linear search through the 3-entry suo dict
        to find the entry that is determining the element usage at index.
        """
        assert self.closed
        if index < self.suo[U]:
            return U
        elif index < self.suo[S]:
            return S
        elif index < self.suo[O]:
            return O
        else:
            return N

    def set_used_at(self, index, u: Used = U):
        """Set usage at specified index.
        """
        assert self.closed
        self.suo[u] = max(self.suo[u], index)
        self.closure()

    def __repr__(self):
        non_zero_uppers = []
        for el in [U, S, O]:
            if self.suo[el]:
                non_zero_uppers.append(f"{el.name}@0:{self.suo[el]}")
        return f"({', '.join(non_zero_uppers)})"

    def default(self):
        self._suo = OrderedDict([
            (S, 0),
            (U, 0),
            (O, 0)
        ])
        return self

    def bottom(self):
        self._suo = OrderedDict([
            (S, 0),
            (U, 0),
            (O, 0)
        ])
        return self

    def top(self):
        self._suo = OrderedDict([
            (S, 0),
            (U, 0),
            (O, 0)
        ])
        return self

    def is_bottom(self) -> bool:
        return all(upper == 0 for upper in self.suo.values())

    def is_top(self) -> bool:
        return all(upper == inf for upper in self.suo.values())

    def _less_equal(self, other: 'UsedListStartLattice') -> bool:
        return all(s1 <= s2 for s1, s2 in zip(self.suo.values(), other.suo.values()))

    def _meet(self, other: 'UsedListStartLattice'):
        for u in [S, U, O]:
            self.suo[u] = min(self.suo[u], other.suo[u])
        return self

    def _join(self, other: 'UsedListStartLattice') -> 'UsedListStartLattice':
        for u in [S, U, O]:
            self.suo[u] = max(self.suo[u], other.suo[u])
        return self

    def _widening(self, other: 'UsedListStartLattice'):
        return self._join(other)

    @property
    def closed(self):
        return (self.suo[S] == 0 or self.suo[O] == 0) \
               and (not self.suo[U] >= self.suo[S] or self.suo[S] == 0) \
               and (not self.suo[U] >= self.suo[O] or self.suo[O] == 0)

    def closure(self):
        suo = self.suo
        # check for each index individually if it has to be adjusted
        if suo[S] <= suo[O] or suo[S] <= suo[U]:
            suo[S] = 0
        if suo[S] > 0 and suo[O] > 0:
            suo[U] = max(suo[S], suo[O])
        if suo[O] <= suo[S] or suo[O] <= suo[U]:
            suo[O] = 0

        assert self.closed
        return self

    # noinspection PyPep8Naming
    def change_S_to_U(self):
        """Change previously S-annotated (used in outer scope) to U-annotated (definitely used)"""
        self.suo[U] = max(self.suo[U], self.suo[S])
        self.suo[S] = 0

    # noinspection PyPep8Naming
    def change_SU_to_O(self):
        """Change previously U/S-annotated to O-annotated"""
        self.suo[O] = max(self.suo[U], self.suo[S])
        self.suo[U] = 0
        self.suo[S] = 0

    def descend(self) -> 'UsedListStartLattice':
        assert self.closed

        self.suo[S] = max(self.suo[S], self.suo[U])
        self.suo[U] = 0
        self.suo[O] = 0
        return self

    def combine(self, other: 'UsedListStartLattice') -> 'UsedListStartLattice':
        # This method is generically implemented using the COMBINE dict
        assert self.closed and other.closed

        all_uppers = [(index, used) for used, index in list(self.suo.items()) + list(other.suo.items())]
        all_uppers.sort(key=lambda a: a[0])

        seq = {
            S: [0],
            U: [0],
            O: [0]
        }
        lower = 0
        for upper, used in all_uppers:
            if upper - lower > 0:  # ignore zero-length subsequences
                seq[UsedLattice.COMBINE[(self.used_at(lower), other.used_at(lower))]].append(upper)
                lower = upper

        # take maximal upper for every used element (over-approximation)
        self.suo[S] = max(seq[S])
        self.suo[U] = max(seq[U])
        self.suo[O] = max(seq[O])

        self.closure()

        return self
