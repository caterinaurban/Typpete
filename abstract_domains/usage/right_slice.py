from typing import Optional

from abstract_domains.lattice import BaseLattice
from enum import Flag


class RightSliceLattice(BaseLattice):
    """Used variable analysis core abstract domain representation."""

    def __init__(self, index=0):
        """Used variable analysis core abstract domain representation.
        
        :param used: initial lattice element
        """
        super().__init__()
        self._inf = False
        self._index = -1
        self.index = index  # set again via property to ensure _inf is set correctly

    @property
    def inf(self) -> bool:
        return self._inf

    @property
    def index(self):
        if self.inf:
            return None
        else:
            return self._index

    @index.setter
    def index(self, index: Optional[int]):
        self._inf = index is None
        self._index = index

    def __repr__(self):
        return repr(self.index) or "inf"

    def default(self):
        self.index = 0
        return self

    def bottom(self):
        self.index = 0
        return self

    def top(self):
        self.index = None
        return self

    def is_bottom(self) -> bool:
        return self.index == 0

    def is_top(self) -> bool:
        return self.inf

    def _less_equal(self, other: 'RightSliceLattice') -> bool:
        if other.inf:
            return True
        elif self.inf:
            return False
        else:
            return self.index < other.index

    def _meet(self, other: 'RightSliceLattice'):
        if not self.less_equal(other):
            self.index = other.index
        return self

    def _join(self, other: 'RightSliceLattice') -> 'RightSliceLattice':
        if self.less_equal(other):
            self.index = other.index
        return self

    def _widening(self, other: 'RightSliceLattice'):
        return self._join(other)
