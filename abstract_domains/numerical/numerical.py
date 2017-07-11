from abc import ABCMeta, abstractmethod
from core.expressions import VariableIdentifier, Expression, UnaryArithmeticOperation


# TODO rename (without lattice) e.g. IntegerOperations or Values or do not provide interface
class NumericalLattice(metaclass=ABCMeta):
    @abstractmethod
    def add(self, other):
        pass

    @abstractmethod
    def sub(self, other):
        pass

    @abstractmethod
    def mult(self, other):
        pass

    @abstractmethod
    def negate(self):
        pass

    @classmethod
    def evaluate(cls, expr: Expression):
        """Evaluates the expression within this abstract domain."""
        raise NotImplementedError()


# rename NumericalMixin
class NumericalDomain(metaclass=ABCMeta):
    # TODO maybe remove it from interface completely
    @abstractmethod
    def forget(self, var: VariableIdentifier):
        """Forget all constraints about a variable."""

    @abstractmethod
    def set_bounds(self, var: VariableIdentifier, lower: int, upper: int):
        """Sets the upper and lower bound of a variable.
        
        :param var: the variable of interest
        :param lower: the upper bound of ``var``
        :param upper: the lower bound of ``var``"""

    @abstractmethod
    def get_bounds(self, var: VariableIdentifier):
        """Returns the upper and lower bound of a variable.
        
        :param var: the variable of interest
        :return: A tuple (lower, upper) of the bounds of ``var``"""

    @abstractmethod
    def evaluate(self, expr: Expression):
        """Evaluates the expression within this abstract domain."""
