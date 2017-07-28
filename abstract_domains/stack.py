from abc import ABCMeta, abstractmethod
from typing import Type, Dict, Any
from abstract_domains.lattice import BoundedLattice


class Stack(BoundedLattice, metaclass=ABCMeta):
    """A stack of elements of a lattice L."""

    def __init__(self, lattice: Type, arguments: Dict[str, Any]):
        """Create a stack of lattice elements lattice L.

        :param lattice: type of lattice elements L
        """
        super().__init__()
        self._stack = [lattice(**arguments)]

    @property
    def stack(self):
        return self._stack

    def __repr__(self):
        return " | ".join(map(repr, self.stack))

    @abstractmethod
    def push(self):
        """Push an element on the stack."""

    @abstractmethod
    def pop(self):
        """Pop an element from the stack."""

    def _less_equal(self, other: 'Stack') -> bool:
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        return all(l.less_equal(r) for l, r in zip(self.stack, other.stack))

    def _join(self, other: 'Stack') -> 'Stack':
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.join(other.stack[i])
        return self

    def _meet(self, other: 'Stack'):
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, item in enumerate(self.stack):
            item.meet(other.stack[i])
        return self

    def _widening(self, other: 'Stack'):
        return self._join(other)
