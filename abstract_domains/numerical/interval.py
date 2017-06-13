from abstract_domains.generic_lattices import StoreLattice
from abstract_domains.lattice import BottomElementMixin
from abstract_domains.numerical.numerical import NumericalDomain, NumericalLattice
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from core.expressions_tools import ExpressionVisitor


class IntervalLattice(BottomElementMixin, NumericalLattice):
    def __init__(self, lower=inf, upper=-inf):
        """Create an Interval Lattice for a single variable.
        """
        self._lower = lower
        self._upper = upper
        super().__init__()

    def add(self, other):
        return IntervalLattice(self.lower + other.lower, self.upper + other.upper)

    def sub(self, other):
        return IntervalLattice(self.lower - other.upper, self.upper - other.lower)

    def mul(self, other):
        comb = [self.lower * other.lower, self.lower * other.upper, self.upper * other.lower, self.upper * other.upper]
        return IntervalLattice(min(comb), max(comb))

    def negate(self):
        return IntervalLattice(min(-self.lower, -self.upper), max(-self.lower, -self.upper))

    @property
    def lower(self):
        return self._lower

    @lower.setter
    def lower(self, b):
        self._lower = b

    @property
    def upper(self):
        return self._upper

    @upper.setter
    def upper(self, b):
        self._upper = b

    def __repr__(self):
        return f"[{self.lower},{self.upper}]"

    def default(self):
        self.top()
        return self

    def top(self):
        self.lower = -inf
        self.upper = inf
        return self

    def is_top(self) -> bool:
        return self.lower == -inf and self.upper == inf

    def _less_equal(self, other: 'IntervalLattice') -> bool:
        return other.lower <= self.lower and self.upper <= other.upper

    def _meet(self, other: 'IntervalLattice'):
        self.lower = max(self.lower, other.lower)
        self.upper = min(self.upper, other.upper)
        if self.lower > self.upper:
            self.bottom()
        return self

    def _join(self, other: 'IntervalLattice') -> 'IntervalLattice':
        self.lower = min(self.lower, other.lower)
        self.upper = max(self.upper, other.upper)
        return self

    def _widening(self, other: 'IntervalLattice'):
        if other.lower < self.lower:
            self.lower = inf
        if other.upper > self.upper:
            self.upper = inf
        return self


class IntervalStore(StoreLattice, NumericalDomain):
    class IntervalVisitor(ExpressionVisitor):
        def __init__(self, interval_store):
            self._store = interval_store  # keep a reference to container interval store

        @property
        def store(self):
            return self._store

        def generic_visit(self, expr):
            raise NotImplementedError(
                "IntervalStore does not support generic visit of expressions! Define handling for each expression explicitly!")

        def visit_Input(self, expr: Input):
            return IntervalLattice()

        def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation):
            l = self.visit(expr.left)
            r = self.visit(expr.right)
            if expr.operator == BinaryArithmeticOperation.Operator.Add:
                return l.add(r)
            elif expr.operator == BinaryArithmeticOperation.Operator.Sub:
                return l.sub(r)
            elif expr.operator == BinaryArithmeticOperation.Operator.Mult:
                return l.mult(r)
            else:
                raise NotImplementedError()

        def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation):
            r = self.visit(expr.expression)
            if expr.operator == UnaryArithmeticOperation.Operator.Add:
                return r.negate()
            elif expr.operator == UnaryArithmeticOperation.Operator.Sub:
                return r
            else:
                raise NotImplementedError()

        def visit_Literal(self, expr: Literal):
            if expr.typ == int:
                c = int(expr.val)
                return IntervalLattice(c, c)
            else:
                raise ValueError()

        def visit_VariableIdentifier(self, expr: VariableIdentifier):
            if expr.typ == int:
                return self.store.variables[expr.name]
            else:
                raise ValueError()

    def __init__(self, variables: List[VariableIdentifier]):
        super().__init__(variables, {int: IntervalLattice})

    def forget(self, var: VariableIdentifier):
        self.variables[var].top()

    def set_variable_constant(self, var: VariableIdentifier, constant):
        self.variables[var].lower = constant
        self.variables[var].upper = constant

    def set_expression_constant(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_variable_lb(self, var: VariableIdentifier, constant):
        self.variables[var].lower = constant

    def set_variable_ub(self, var: VariableIdentifier, constant):
        self.variables[var].upper = constant

    def set_expression_lb(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_expression_ub(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_variable_difference_ub(self, var1: VariableIdentifier, var2: VariableIdentifier, constant):
        raise NotImplementedError()

    def set_expression_difference_ub(self, expr1: Expression, expr2: Expression, constant):
        raise NotImplementedError()

    def evaluate_expression(self, expr: Expression):


class IntervalDomain(IntervalStore, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.

        :param variables: list of program variables
        """
        super().__init__(variables)
        self._visitor = Octagon.OctagonVisitor(self)

    def _substitute_variable(self, left: Expression, right: Expression) -> 'State':
        raise NotImplementedError()

    def _assume(self, condition: Expression) -> 'State':
        return self

    def exit_if(self) -> 'State':
        return self

    def exit_loop(self) -> 'State':
        return self

    def _output(self, output: Expression) -> 'State':
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return self

    def enter_if(self) -> 'State':
        return self

    def enter_loop(self) -> 'State':
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return self

    def _assign_variable(self, left: Expression, right: Expression) -> 'State':
        # Octagonal Assignments
        if isinstance(left, VariableIdentifier):
            if isinstance(right, Literal):
                if right.typ == int:
                    c = int(right.val)
                    self.set_variable_constant(left, right)
                else:
                    raise ValueError()

        return self
