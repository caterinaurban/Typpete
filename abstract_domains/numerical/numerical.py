from abc import ABCMeta, abstractmethod
from core.expressions import VariableIdentifier, Expression, UnaryArithmeticOperation

# rename (without lattice) e.g. IntegerOperations
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

    # TODO assume

    # TODO assign

    # TODO substitute

    # TODO create_variable (also in state interface)

    # TODO remove_variable (also in state interface)

    # TODO query bounds (interval)

    @abstractmethod
    def evaluate(self, expr: Expression):
        """Evaluates the expression within this abstract domain."""
