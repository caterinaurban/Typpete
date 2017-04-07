from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce
from typing import List


class Lattice(ABC):
    class Kind(Enum):
        """Kind of a lattice element."""
        Bottom = -1  # bottom element
        Default = 0
        Top = 1  # top element

    class Internal(object):
        def __init__(self, kind: 'Lattice.Kind'):
            """Lattice internal representation.

            :param kind: kind of lattice element
            """
            self._kind = kind

        @property
        def kind(self):
            return self._kind

    def __init__(self, kind: Kind = Kind.Default):
        """Lattice representation.
        Account for lattice operations by modifying the current internal representation.

        :param kind: kind of lattice element
        """
        self._internal = Lattice.Internal(kind)

    @property
    def internal(self):
        return self._internal

    @property
    def kind(self):
        return self.internal.kind

    @classmethod
    def bottom(cls):
        """Create a new bottom lattice element. 

        :return: new bottom lattice element
        """
        return type(cls)(Lattice.Kind.Bottom)

    @classmethod
    def top(cls):
        """Create a new top lattice element.

        :return: new top lattice element
        """
        return type(cls)(Lattice.Kind.Top)

    def is_bottom(self):
        """Test whether the lattice element is bottom.

        :return: whether the lattice element is bottom
        """
        return self.kind == Lattice.Kind.Bottom

    def is_top(self):
        """Test whether the lattice element is top.

        :return: whether the lattice element is top
        """
        return self.kind == Lattice.Kind.Top

    @abstractmethod
    def less_equal_default(self, other: 'Lattice') -> bool:
        """Partial order between default lattice elements.

        :param other: other lattice element
        :return: whether the current lattice element is less than or equal to the other lattice element 
        """

    def less_equal(self, other: 'Lattice') -> bool:
        """Partial order between lattice elements.

        :param other: other lattice element
        :return: whether the current lattice element is less than or equal to the other lattice element 
        """
        return self.is_bottom() or other.is_top() or self.less_equal_default(other)

    @abstractmethod
    def join_default(self, other: 'Lattice') -> 'Lattice':
        """Least upper bound between default lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to the least upper bound of the two lattice elements
        """

    def join(self, other: 'Lattice') -> 'Lattice':
        """Least upper bound between lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the least upper bound of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        elif other.is_bottom() or self.is_top():
            return self
        else:
            return self.join_default(other)

    def big_join(self, elements: List['Lattice']) -> 'Lattice':
        """Least upper bound between multiple lattice elements

        :param elements: lattice elements to compute the least upper bound of
        :return: current lattice element modified to be the least upper bound of the lattice elements
        """
        return reduce(lambda s1, s2: s1.join(s2), elements, self.replace(self.bottom()))

    @abstractmethod
    def meet_default(self, other: 'Lattice'):
        """Greatest lower bound between default lattice elements.

        :param other: other lattice element 
        :return: current lattice element modified to be the greatest lower bound of the two lattice elements
        """

    def meet(self, other: 'Lattice'):
        """Greatest lower bound between lattice elements.

        :param other: other lattice element 
        :return: current lattice element modified to be the greatest lower bound of the two lattice elements
        """
        if self.is_top() or other.is_bottom():
            return self.replace(other)
        elif other.is_top() or self.is_bottom():
            return self
        else:
            return self.meet_default(other)

    def big_meet(self, elements: List['Lattice']) -> 'Lattice':
        """Greatest lower bound between multiple lattice elements

        :param elements: lattice elements to compute the greatest lower bound of
        :return: current lattice element modified to be the least upper bound of the lattice elements
        """
        return reduce(lambda s1, s2: s1.meet(s2), elements, self.replace(self.top()))

    @abstractmethod
    def widening_default(self, other: 'Lattice'):
        """Widening between default lattice elements.

        :param other: other lattice element 
        :return: current lattice element modified to be the widening of the two lattice elements
        """

    def widening(self, other: 'Lattice'):
        """Widening between lattice elements.

        :param other: other lattice element 
        :return: current lattice element modified to be the widening of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        else:
            return self.widening_default(other)

    def replace(self, other: 'Lattice') -> 'Lattice':
        """Replace the current internal representation with the internal representation of another lattice element.

        :param other: other lattice element
        :return: current lattice element with replaced internal representation
        """
        self._internal = other._internal
        return self
