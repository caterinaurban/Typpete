from abc import ABCMeta, abstractmethod

from core.expressions import VariableIdentifier, Expression


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


class NumericalDomain(metaclass=ABCMeta):
    @abstractmethod
    def forget(self, var: VariableIdentifier):
        """Forget all constraints about a variable."""

    @abstractmethod
    def set_variable_constant(self, var: VariableIdentifier, constant):
        """Sets the variable to a constant value: `x = c`."""

    @abstractmethod
    def set_expression_constant(self, expr: Expression, constant):
        """Sets the expression to a constant value: `e = c`."""

    @abstractmethod
    def set_variable_lb(self, var: VariableIdentifier, constant):
        """Sets the lower bound of a variable: `c <= x`."""

    @abstractmethod
    def set_variable_ub(self, var: VariableIdentifier, constant):
        """Sets the lower bound of a variable: `x <= c`."""

    @abstractmethod
    def set_expression_lb(self, expr: Expression, constant):
        """Sets the lower bound of an expression: `c <= e`."""

    @abstractmethod
    def set_expression_ub(self, expr: Expression, constant):
        """Sets the upper bound of an expression: `e <= c`."""

    @abstractmethod
    def set_variable_difference_ub(self, var1: VariableIdentifier, var2: VariableIdentifier, constant):
        """Sets the difference upper bound for two variables: `x - y <= c`."""

    @abstractmethod
    def set_expression_difference_ub(self, expr1: Expression, expr2: Expression, constant):
        """Sets the difference upper bound for two expressions: `e1 - e2 <= c`."""

    @abstractmethod
    def evaluate_expression(self, expr: Expression):
        """Evaluates the expression within this abstract domain."""
