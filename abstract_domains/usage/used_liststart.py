from abstract_domains.lattice import BaseLattice

from abstract_domains.usage.used import U, S, O, N, UsedLattice
from collections import OrderedDict


class UsedListStartLattice(BaseLattice):
    """Used variable analysis core abstract domain representation."""

    def __init__(self, s=0, u=0, o=0):
        """Used variable analysis core abstract domain representation.
        
        :param used: initial lattice element
        """
        super().__init__()
        self._suo = OrderedDict(
            [
                (S, s),
                (U, u),
                (O, o)
            ]
        )

    @property
    def suo(self):
        return self._suo

    def used_at(self, index):
        """Finds Used-element at specified index.
        
        Does a linear search through the 3-entry suo dict
        to find the entry that is determining the element at index.
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

    def __repr__(self):
        return repr(self.suo)

    def default(self):
        self._suo = OrderedDict(
            (S, 0),
            (U, 0),
            (O, 0)
        )
        return self

    def bottom(self):
        self._suo = OrderedDict(
            (S, 0),
            (U, 0),
            (O, 0)
        )
        return self

    def top(self):
        self._suo = OrderedDict(
            (S, 0),
            (U, 0),
            (O, 0)
        )
        return self

    def is_bottom(self) -> bool:
        return all(slice.is_bottom() for slice in self.suo.values())

    def is_top(self) -> bool:
        return all(slice.is_top() for slice in self.suo.values())

    def _less_equal(self, other: 'UsedListStartLattice') -> bool:
        return all(s1.less_equal(s2) for s1, s2 in zip(self.suo.values(), other.suo.values()))

    def _meet(self, other: 'UsedListStartLattice'):
        for s1, s2 in zip(self.suo.values(), other.suo.values()):
            s1.meet(s2)
        return self

    def _join(self, other: 'UsedListStartLattice') -> 'UsedListStartLattice':
        for s1, s2 in zip(self.suo.values(), other.suo.values()):
            s1.join(s2)
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

    def descend(self) -> 'UsedListStartLattice':
        assert self.closed

        self.suo[S] = max(self.suo[S], self.suo[U])
        self.suo[U] = 0
        self.suo[O] = 0
        return self

    def combine(self, other: 'UsedListStartLattice') -> 'UsedListStartLattice':
        # This method is generically implemented using the COMBINE dict
        # it uses a more powerful representation first:
        # multiple (maximum 4) consequent sequences with an associated used element
        # then it is mapped to SUO representation

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
