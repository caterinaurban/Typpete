from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import reduce
from typing import List, TypeVar, Generic

L = TypeVar('L')


class BaseLattice(metaclass=ABCMeta):
    """
    The most generic lattice (element) that defines a flexible, abstract interface.

    An instance of this class represents a mutable lattice element.

    Subclassing lattices are expected to provide consistent methods:

    * `default()`
    * `bottom()`, `is_bottom()`
    * `top()`, `is_top()`
    """

    def __init__(self):
        """Create a default lattice element."""
        self.default()

    def __eq__(self, other: 'BaseLattice'):
        if isinstance(other, self.__class__):
            return repr(self) == repr(other)
        return False

    def __hash__(self):
        return hash(repr(self))

    def __ne__(self, other: 'BaseLattice'):
        return not (self == other)

    @abstractmethod
    def __repr__(self):
        """Unambiguous string representing the current lattice element.

        :return: unambiguous representation string
        """

    @abstractmethod
    def default(self):
        """Set to the default lattice element.

        :return: current lattice element modified to be the default lattice element
        """

    @abstractmethod
    def bottom(self):
        """Set to the bottom lattice element.

        :return: current lattice element modified to be the bottom lattice element
        """

    @abstractmethod
    def top(self):
        """Set to the top lattice element.

        :return: current lattice element modified to be the top lattice element
        """

    @abstractmethod
    def is_bottom(self) -> bool:
        """Test whether the lattice element is bottom.

        :return: whether the lattice element is bottom
        """

    @abstractmethod
    def is_top(self) -> bool:
        """Test whether the lattice element is top.

        :return: whether the lattice element is top
        """

    @abstractmethod
    def _less_equal(self, other: 'BaseLattice') -> bool:
        """Partial order between default lattice elements.

        :param other: other lattice element
        :return: whether the current lattice element is less than or equal to the other lattice element
        """

    def less_equal(self, other: 'BaseLattice') -> bool:
        """Partial order between lattice elements.

        :param other: other lattice element
        :return: whether the current lattice element is less than or equal to the other lattice element
        """
        if self.is_bottom() or other.is_top():
            return True
        elif other.is_bottom() or self.is_top():
            return False
        else:
            return self._less_equal(other)

    @abstractmethod
    def _join(self, other: 'BaseLattice') -> 'BaseLattice':
        """Least upper bound between default lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the least upper bound of the two lattice elements
        """

    def join(self, other: 'BaseLattice') -> 'BaseLattice':
        """Least upper bound between lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the least upper bound of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        elif other.is_bottom() or self.is_top():
            return self
        else:
            return self._join(other)

    def big_join(self, elements: List['BaseLattice']) -> 'BaseLattice':
        """Least upper bound between multiple lattice elements

        :param elements: lattice elements to compute the least upper bound of
        :return: current lattice element modified to be the least upper bound of the lattice elements
        """
        return reduce(lambda s1, s2: s1.join(s2), elements, self.bottom())

    @abstractmethod
    def _meet(self, other: 'BaseLattice'):
        """Greatest lower bound between default lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the greatest lower bound of the two lattice elements
        """

    def meet(self, other: 'BaseLattice'):
        """Greatest lower bound between lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the greatest lower bound of the two lattice elements
        """
        if self.is_top() or other.is_bottom():
            return self.replace(other)
        elif other.is_top() or self.is_bottom():
            return self
        else:
            return self._meet(other)

    def big_meet(self, elements: List['BaseLattice']) -> 'BaseLattice':
        """Greatest lower bound between multiple lattice elements

        :param elements: lattice elements to compute the greatest lower bound of
        :return: current lattice element modified to be the least upper bound of the lattice elements
        """
        return reduce(lambda s1, s2: s1.meet(s2), elements, self.top())

    @abstractmethod
    def _widening(self, other: 'BaseLattice'):
        """Widening between default lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the widening of the two lattice elements
        """

    def widening(self, other: 'BaseLattice'):
        """Widening between lattice elements.

        :param other: other lattice element
        :return: current lattice element modified to be the widening of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return self.replace(other)
        else:
            return self._widening(other)

    def replace(self, other: 'BaseLattice') -> 'BaseLattice':
        """Replace this instance with another lattice element.

        :param other: other lattice element
        :return: current lattice element updated to be equal to other
        """
        self.__dict__.update(other.__dict__)
        assert self == other, f"after replace call, {self} is not equals {other}"
        return self


class Kind(Enum):
    TOP = 3
    ELEMENT = 2
    BOTTOM = 1


class SpecialElementMixin(BaseLattice, Generic[L], metaclass=ABCMeta):
    """A Mixin to add a capability to distinguish between user-defined and special elements like TOP/BOTTOM."""

    def __init__(self):
        """Create a default lattice element."""
        self._element = None
        self._kind = Kind.ELEMENT
        super().__init__()

    @property
    def element(self):
        return self._element

    @element.setter
    def element(self, element):
        self._kind = Kind.ELEMENT
        self._element = element

    def __repr__(self):
        return str(self.element) if self._kind is Kind.ELEMENT else self._kind.name


class TopElementMixin(SpecialElementMixin, BaseLattice, Generic[L], metaclass=ABCMeta):
    """A Mixin to add a special TOP element to another lattice."""

    def top(self) -> 'Lattice[L]':
        self._kind = Kind.TOP
        self._element = None
        return self

    def is_top(self) -> bool:
        return self._kind == Kind.TOP


class BottomElementMixin(SpecialElementMixin, BaseLattice, Generic[L], metaclass=ABCMeta):
    """A Mixin to add a special BOTTOM element to another lattice."""

    def bottom(self) -> 'Lattice[L]':
        self._kind = Kind.BOTTOM
        self._element = None
        return self

    def is_bottom(self) -> bool:
        return self._kind == Kind.BOTTOM


class Lattice(TopElementMixin, BottomElementMixin, BaseLattice, Generic[L], metaclass=ABCMeta):
    """
    A generic lattice that provides a TOP and a BOTTOM element and related methods.

    If you want to provide the TOP/BOTTOM element yourself, subclass `BaseLattice` instead.

    An instance of this class represents a mutable lattice element.

    Subclassing lattices are expected to provide the method:

    * `default()`

    **Note**: Subclasses must ensure that the `kind` property is set appropriately at any point in time. This is 
    guaranteed when using only the `element` property to set the element. 
    """
