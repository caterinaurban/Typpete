from abc import ABCMeta, abstractmethod
from core.expressions import VariableIdentifier, Expression, UnaryArithmeticOperation


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
    def evaluate_expression(cls, expr: Expression):
        """Evaluates the expression within this abstract domain."""
        raise NotImplementedError()


class NumericalDomain(metaclass=ABCMeta):
    @abstractmethod
    def forget(self, var: VariableIdentifier):
        """Forget all constraints about a variable."""

    def set_variable_constant(self, var: VariableIdentifier, constant):
        """Sets the variable to a constant value: `x = c`."""
        raise NotImplementedError()

    def set_variable_lb(self, var: VariableIdentifier, constant):
        """Sets the lower bound of a variable: `c <= x`."""
        raise NotImplementedError()

    def set_variable_ub(self, var: VariableIdentifier, constant):
        """Sets the lower bound of a variable: `x <= c`."""
        raise NotImplementedError()

    def set_octagonal_constraint(self, sign1: UnaryArithmeticOperation.Operator, var1: VariableIdentifier,
                                 sign2: UnaryArithmeticOperation.Operator,
                                 var2: VariableIdentifier, constant):
        """Sets the octagonal constraint for two variables: `+/- x +/- y <= c`."""
        raise NotImplementedError()

    @abstractmethod
    def evaluate_expression(self, expr: Expression):
        """Evaluates the expression within this abstract domain."""
