"""
Store
=====

Lifting of a lattice to a set of program variables.
"""


from typing import List, Type, Dict, Any
from collections import defaultdict
from abstract_domains.lattice import Lattice
from core.expressions import VariableIdentifier
from core.utils import copy_docstring


class Store(Lattice):
    """Mutable element of a store ``Var -> L``, lifting a lattice ``L`` to a set of program variables ``Var``.

    .. warning::
        Lattice operations modify the current store.

    .. document private methods
    .. automethod:: Store._less_equal
    .. automethod:: Store._meet
    .. automethod:: Store._join
    """
    def __init__(self, variables: List[VariableIdentifier], lattices: Dict[Type, Type[Lattice]],
                 arguments: Dict[Type, Dict[str, Any]] = defaultdict(lambda: dict())):
        """Create a mapping Var -> L from each variable in Var to the corresponding lattice element in L.

        :param variables: list of program variables
        :param lattices: dictionary mapping each variable type to the corresponding lattice type
        :param arguments: dictionary mapping each variable type to the arguments of the corresponding lattice type
        """
        super().__init__()
        self._variables = variables
        self._lattices = lattices
        self._arguments = arguments
        self._store = {var: self._lattices[var.typ](**self._arguments[var.typ]) for var in self._variables}

    @property
    def variables(self):
        """Variables of the current store."""
        return self._variables

    @property
    def store(self):
        """Current mapping from variables to their corresponding lattice element."""
        return self._store

    def __repr__(self):
        return ", ".join("{} -> {}".format(variable, value) for variable, value in self.store.items())

    @copy_docstring(Lattice.bottom)
    def bottom(self) -> 'Store':
        for var in self.store:
            self.store[var].bottom()
        return self

    @copy_docstring(Lattice.top)
    def top(self) -> 'Store':
        for var in self.store:
            self.store[var].top()
        return self

    @copy_docstring(Lattice.is_bottom)
    def is_bottom(self) -> bool:
        """The current store is bottom if `any` of its variables map to a bottom element."""
        return any(element.is_bottom() for element in self.store.values())

    @copy_docstring(Lattice.is_top)
    def is_top(self) -> bool:
        """The current store is top if `all` of its variables map to a top element."""
        return all(element.is_top() for element in self.store.values())

    @copy_docstring(Lattice._less_equal)
    def _less_equal(self, other: 'Store') -> bool:
        """The comparison is performed point-wise for each variable."""
        return all(self.store[var].less_equal(other.store[var]) for var in self.store)

    @copy_docstring(Lattice._meet)
    def _meet(self, other: 'Store'):
        """The meet is performed point-wise for each variable."""
        for var in self.store:
            self.store[var].meet(other.store[var])
        return self

    @copy_docstring(Lattice._join)
    def _join(self, other: 'Store') -> 'Store':
        """The join is performed point-wise for each variable."""
        for var in self.store:
            self.store[var].join(other.store[var])
        return self

    @copy_docstring(Lattice._widening)
    def _widening(self, other: 'Store'):
        return self._join(other)
