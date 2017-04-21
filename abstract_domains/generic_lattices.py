from abc import ABC, abstractmethod
from abstract_domains.lattice import Lattice
from core.expressions import Expression, VariableIdentifier
from enum import Enum
from typing import List, Set, TypeVar, Generic, Type
from copy import deepcopy

L = TypeVar('L', Lattice, Lattice)  # TODO not sure if it is ok to reuse that typevar for different purposes


class TopBottomLattice(Lattice, Generic[L], ABC):
    """
    A generic lattice that extends a subclassing lattice with a TOP and a BOTTOM element.
    """

    class Kind(Enum):
        TOP = 3
        ELEMENT = 2
        BOTTOM = 1

    def __init__(self, initial_element: L = None):
        """Create a lattice element.

        :param initial_element: initial lattice element (if None, the lattice default() method is used to set the default element)
        """
        super().__init__()
        if initial_element is not None:
            self._kind = TopBottomLattice.Kind.ELEMENT
            self._element = initial_element
        else:
            self.default()

    @property
    def element(self):
        return self._element

    @element.setter
    def element(self, element):
        self._kind = TopBottomLattice.Kind.ELEMENT
        self._element = element

    def __repr__(self):
        return str(self.element) if self._kind is TopBottomLattice.Kind.ELEMENT else self._kind.name

    def bottom(self) -> 'TopBottomLattice[L]':
        self._kind = TopBottomLattice.Kind.BOTTOM
        self._element = None
        return self

    def top(self) -> 'TopBottomLattice[L]':
        self._kind = TopBottomLattice.Kind.TOP
        self._element = None
        return self

    def is_bottom(self) -> bool:
        return self._kind == TopBottomLattice.Kind.BOTTOM

    def is_top(self) -> bool:
        return self._kind == TopBottomLattice.Kind.TOP


class StoreLattice(Lattice, Generic[L]):
    """A generic lattice that represents a mapping Var -> L for some other lattice L."""

    def __init__(self, variables: List[VariableIdentifier], element_lattice: Type[L]):
        """Create a store lattice that represents a mapping Var -> L for some other lattice L.

        :param variables: list of program variables
        :param element_lattice: type of lattice elements L
        """
        self._variables_list = variables
        self._element_lattice = element_lattice
        self._variables = None
        self.default()

    @property
    def variables(self):
        return self._variables

    def __repr__(self):
        variables = "\n".join("{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return variables

    def default(self):
        self._variables = {variable: self._element_lattice().default() for variable in self._variables_list}
        return self

    def bottom(self) -> 'StoreLattice[L]':
        self._variables = {variable: self._element_lattice().bottom() for variable in self._variables}
        return self

    def top(self) -> 'StoreLattice[L]':
        self._variables = {variable: self._element_lattice().top() for variable in self._variables}
        return self

    def is_bottom(self) -> bool:
        return all(element.is_bottom() for element in self.variables.values())

    def is_top(self) -> bool:
        return all(element.is_top() for element in self.variables.values())

    def _less_equal(self, other: 'StoreLattice[L]') -> bool:
        return all(self.variables[var].less_equal(other.variables[var]) for var in self.variables)

    def _meet(self, other: 'StoreLattice[L]'):
        for var in self.variables:
            self.variables[var].meet(other.variables[var])
        return self

    def _join(self, other: 'StoreLattice[L]') -> 'StoreLattice[L]':
        for var in self.variables:
            self.variables[var].join(other.variables[var])
        return self

    def _widening(self, other: 'StoreLattice[L]'):
        return self._join(other)


class StackLattice(TopBottomLattice, ABC):
    """A generic lattice that represents a stack of elements of some other lattice L."""

    def __init__(self, element_lattice: Type[L], args_dict):
        """Create a stack lattice of elements of some other lattice L.

        :param element_lattice: type of lattice elements L
        """
        self._args_dict = args_dict
        self._element_lattice = element_lattice
        self._stack = None
        self.default()

    @property
    def stack(self):
        return self._stack

    def __repr__(self):
        return " | ".join(map(repr, self.stack))

    def default(self):
        self._stack = [self._element_lattice(**self._args_dict).default()]
        return self

    @abstractmethod
    def push(self):
        """push an element on the stack"""

    @abstractmethod
    def pop(self):
        """pop an element from the stack"""

    def _less_equal(self, other: 'StackLattice[L]') -> bool:
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        return all(l.less_equal(r) for l, r in zip(self.stack, other.stack))

    def _meet(self, other: 'StackLattice[L]'):
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.meet(other.stack[i])
        return self

    def _join(self, other: 'StackLattice[L]') -> 'StackLattice[L]':
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.join(other.stack[i])
        return self

    def _widening(self, other: 'StackLattice[L]'):
        return self._join(other)
