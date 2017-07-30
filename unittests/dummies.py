from typing import List, Set

from abstract_domains.store import Store
from abstract_domains.lattice import BoundedLattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier


class ExpressionLattice(BoundedLattice):
    """A Lattice representing an expression or top if expression is ambiguous, bottom if not yet set."""

    def __init__(self):
        self._expr = None
        super().__init__()

    def __repr__(self):
        return str(self._expr)

    def _meet(self, other: 'ExpressionLattice'):
        return self if self == other else self.bottom()

    def _join(self, other: 'ExpressionLattice') -> 'ExpressionLattice':
        return self if self == other else self.top()

    def _less_equal(self, other: 'ExpressionLattice') -> bool:
        return self == other

    def _widening(self, other: 'ExpressionLattice'):
        return self.top()


class ExpressionStore(Store, State):
    """A store that saves the current untouched expression for each variable (if possible)."""

    def __init__(self, variables: List[VariableIdentifier]):
        super().__init__(variables, {int: ExpressionLattice})

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'ExpressionStore':
        if isinstance(left, VariableIdentifier):
            self.store[left] = right
        else:
            raise NotImplementedError("")
        return self

    def _assume(self, condition: Expression) -> 'ExpressionStore':
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_loop(self):
        return self  # nothing to be done

    def exit_loop(self):
        return self  # nothing to be done

    def enter_if(self):
        return self  # nothing to be done

    def exit_if(self):
        return self  # nothing to be done

    def _output(self, output: Expression) -> 'ExpressionStore':
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression):
        raise NotImplementedError("")
