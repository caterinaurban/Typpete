from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from expressions import Expression, Constant, VariableIdentifier
from typing import Set


class Lattice(ABC):
    class Kind(Enum):
        """Kind of a lattice element."""
        Bottom = -1     # bottom element
        Default = 0
        Top = 1         # top element

    def __init__(self, kind: Kind):
        """Lattice structure representation.
        Account for lattice operations by creating a new lattice element.
        
        :param kind: kind of lattice element
        """
        self._kind = kind

    @property
    def kind(self):
        return self._kind

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
        :return: new lattice element which is the least upper bound of the two lattice elements
        """

    def join(self, other: 'Lattice') -> 'Lattice':
        """Least upper bound between lattice elements.
        
        :param other: other lattice element
        :return: new lattice element which is the least upper bound of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return copy(other)
        elif other.is_bottom() or self.is_top():
            return copy(self)
        else:
            return self.join_default(other)

    @abstractmethod
    def meet_default(self, other: 'Lattice'):
        """Greatest lower bound between default lattice elements.

        :param other: other lattice element 
        :return: new lattice element which is the greatest lower bound of the two lattice elements
        """

    def meet(self, other: 'Lattice'):
        """Greatest lower bound between lattice elements.
        
        :param other: other lattice element 
        :return: new lattice element which is the greatest lower bound of the two lattice elements
        """
        if self.is_top() or other.is_bottom():
            return copy(other)
        elif other.is_top() or self.is_bottom():
            return copy(self)
        else:
            return self.meet_default(other)

    @abstractmethod
    def widening_default(self, other: 'Lattice'):
        """Widening between default lattice elements.

        :param other: other lattice element 
        :return: new lattice element which is the widening of the two lattice elements
        """

    def widening(self, other: 'Lattice'):
        """Widening between lattice elements.
        
        :param other: other lattice element 
        :return: new lattice element which is the widening of the two lattice elements
        """
        if self.is_bottom() or other.is_top():
            return copy(other)
        else:
            return self.widening_default(other)


class State(ABC):
    def __init__(self, result: Set[Expression]):
        """Analysis state representation. 
        Account for statement effects by modifying the current state.
        
        :param result: set of expressions representing the result of the previously analyzed statement 
        """
        self._result = result

    @property
    def result(self):
        return self._result

    @abstractmethod
    def __str__(self):
        """Analysis state string representation.
        
        :return: string representing the analysis state
        """

    @abstractmethod
    def access_variable_value(self, variable: VariableIdentifier) -> Set[Expression]:
        """Retrieve a variable value. Account for side-effects by modifying the current state. 
        
        :param variable: variable to retrieve the value of
        :return: set of expressions representing the variable value
        """

    def access_variable(self, variable: VariableIdentifier) -> 'State':
        """Access a variable.
        
        :param variable: variable to be accesses
        :return: current state modified by the variable access
        """
        self._result = self.access_variable_value(variable)
        return self

    @abstractmethod
    def assign_variable(self, left: Set[Expression], right: Set[Expression]):
        """Assign an expression to a variable
        
        :param left: 
        :param right: 
        :return: 
        """

    @abstractmethod
    def evaluate_constant_value(self, constant: Constant) -> Set[Expression]:
        """Retrieve a constant value. Account for side-effects by modifying the current state.
        
        :param constant: constant to retrieve the value of
        :return: set of expressions representing the constant value
        """

    def evaluate_constant(self, constant: Constant) -> 'State':
        """Evaluate a constant.
        
        :param constant: constant to be evaluated
        :return: current state modified by the constant evaluation
        """
        self._result = self.evaluate_constant_value(constant)
        return self

    @abstractmethod
    def substitute_variable(self, left: Set[Expression], right: Set[Expression]):
        """
        
        :param left: 
        :param right: 
        :return: 
        """
