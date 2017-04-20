from abstract_domains.lattice import Lattice
from core.expressions import Expression, VariableIdentifier
from enum import Enum
from typing import List, Set, TypeVar, Generic, Type

L1 = TypeVar('L1', Lattice, Lattice)


class TopBottomLattice(Lattice, Generic[L1]):
    """
    A generic lattice that extends a subclassing lattice with a TOP and a BOTTOM element.
    """

    class Kind(Enum):
        TOP = 3
        ELEMENT = 2
        BOTTOM = 1

    def __init__(self, initial_element: L1 = None):
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

    def bottom(self):
        self._kind = TopBottomLattice.Kind.BOTTOM
        self._element = None
        return self

    def top(self):
        self._kind = TopBottomLattice.Kind.TOP
        self._element = None
        return self

    def is_bottom(self) -> bool:
        return self._kind == TopBottomLattice.Kind.BOTTOM

    def is_top(self) -> bool:
        return self._kind == TopBottomLattice.Kind.TOP


L = TypeVar('L', Lattice, Lattice)


class StoreLattice(Lattice, Generic[L]):
    def __init__(self, variables: List[VariableIdentifier], element_lattice: Type[L]):
        """A generic lattice that represents a mapping Var -> L for some other lattice L.

        :param variables: list of program variables
        :param element_lattice: type of lattice elements L
        """
        self._element_lattice = element_lattice
        self._variables = {variable: self._element_lattice() for variable in variables}

    @property
    def variables(self):
        return self._variables

    def __repr__(self):
        variables = "\n".join("{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return variables

    def default(self):
        self._variables = {variable: self._element_lattice() for variable in self._variables}
        return self

    def bottom(self) -> bool:
        self._variables = {variable: self._element_lattice().bottom() for variable in self._variables}
        return self

    def top(self) -> bool:
        self._variables = {variable: self._element_lattice().top() for variable in self._variables}
        return self

    def is_bottom(self) -> 'StoreLattice[L]':
        return all(element.is_bottom() for element in self.variables.values())

    def is_top(self) -> 'StoreLattice[L]':
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
