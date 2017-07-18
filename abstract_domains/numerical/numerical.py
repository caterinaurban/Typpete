from abc import ABCMeta, abstractmethod
from core.expressions import VariableIdentifier, Expression


class NumericalMixin(metaclass=ABCMeta):
    """A mixin to add a numeric interface to abstract domains.
    """

    @abstractmethod
    def forget(self, var: VariableIdentifier):
        """Forget all information about a variable."""

    @abstractmethod
    def set_bounds(self, var: VariableIdentifier, lower: int, upper: int):
        """Set the upper and lower bound of a variable.
        
        :param var: the variable of interest
        :param lower: the upper bound of ``var``
        :param upper: the lower bound of ``var``"""

    @abstractmethod
    def get_bounds(self, var: VariableIdentifier):
        """Return the upper and lower bound of a variable.
        
        :param var: the variable of interest
        :return: A tuple (lower, upper) of the bounds of ``var``"""

    @abstractmethod
    def evaluate(self, expr: Expression):
        """Evaluate the expression within this numerical domain."""
