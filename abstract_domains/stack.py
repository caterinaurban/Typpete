"""
Stack
=====

Stack of lattices.
"""

from abc import ABCMeta, abstractmethod
from typing import Type, Dict, Any
from abstract_domains.lattice import BoundedLattice
from core.utils import copy_docstring


class Stack(BoundedLattice, metaclass=ABCMeta):
    """Mutable stack of elements of a lattice.

    .. warning::
        Lattice operations modify the current stack.

    .. document private methods
    .. automethod:: Stack._less_equal
    .. automethod:: Stack._meet
    .. automethod:: Stack._join
    """
    def __init__(self, lattice: Type, arguments: Dict[str, Any]):
        """Create a stack of elements of a lattice.

        :param lattice: type of the lattice
        """
        super().__init__()
        self._stack = [lattice(**arguments)]

    @property
    def stack(self):
        """Current stack of lattice elements."""
        return self._stack

    def __repr__(self):
        return " | ".join(map(repr, self.stack))

    @abstractmethod
    def push(self):
        """Push an element on the current stack."""

    @abstractmethod
    def pop(self):
        """Pop an element from the current stack."""

    @copy_docstring(BoundedLattice._less_equal)
    def _less_equal(self, other: 'Stack') -> bool:
        """The comparison is performed point-wise for each stack element."""
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        return all(l.less_equal(r) for l, r in zip(self.stack, other.stack))

    @copy_docstring(BoundedLattice._meet)
    def _meet(self, other: 'Stack'):
        """The meet is performed point-wise for each stack element."""
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.meet(other.stack[i])
        return self

    @copy_docstring(BoundedLattice._join)
    def _join(self, other: 'Stack') -> 'Stack':
        """The join is performed point-wise for each stack element."""
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.join(other.stack[i])
        return self

    @copy_docstring(BoundedLattice._widening)
    def _widening(self, other: 'Stack'):
        return self._join(other)
