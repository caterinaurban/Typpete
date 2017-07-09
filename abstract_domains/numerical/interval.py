from abstract_domains.generic_lattices import StoreLattice
from abstract_domains.lattice import BottomElementMixin
from abstract_domains.numerical.numerical import NumericalDomain, NumericalLattice
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from core.expressions_tools import ExpressionVisitor


class IntervalLattice(BottomElementMixin, NumericalLattice):
    def __init__(self, lower=-inf, upper=inf):
        """Create an Interval Lattice for a single variable.
        """
        assert lower <= upper
        self._lower = None
        self._upper = None
        super().__init__()
        self._lower = lower
        self._upper = upper

    @property
    def interval(self):
        return self.lower, self.upper

    @interval.setter
    def interval(self, bounds):
        (lower, upper) = bounds
        self.lower = lower
        self.upper = upper

    def add(self, other):
        self.interval = (self.lower + other.lower, self.upper + other.upper)
        return self

    def sub(self, other):
        self.interval = (self.lower - other.upper, self.upper - other.lower)
        return self

    def mult(self, other):
        comb = [self.lower * other.lower, self.lower * other.upper, self.upper * other.lower, self.upper * other.upper]
        self.interval = (min(comb), max(comb))
        return self

    def negate(self):
        self.interval = (min(-self.lower, -self.upper), max(-self.lower, -self.upper))
        return self

    @property
    def lower(self):
        if self.is_bottom():
            raise ValueError("This interval is BOTTOM and has no lower element!")
        return self._lower

    @lower.setter
    def lower(self, b):
        if self.is_bottom():
            raise ValueError("This interval is BOTTOM and has no lower element!")
        self._lower = b

    @property
    def upper(self):
        if self.is_bottom():
            raise ValueError("This interval is BOTTOM and has no upper element!")
        return self._upper

    @upper.setter
    def upper(self, b):
        if self.is_bottom():
            raise ValueError("This interval is BOTTOM and has no upper element!")
        self._upper = b

    def __repr__(self):
        if self.is_bottom():
            return "BOTTOM"
        else:
            return f"[{self.lower},{self.upper}]"

    def default(self):
        self.top()
        return self

    def top(self):
        self.lower = -inf
        self.upper = inf
        return self

    def is_top(self) -> bool:
        return self._lower == -inf and self._upper == inf

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

    @classmethod
    def evaluate(cls, expr: Expression):
        return cls._visitor.visit(expr)

    class Visitor(ExpressionVisitor):
        """A visitor to abstractly evaluate an expression (without variables) in the interval domain."""

        def generic_visit(self, expr):
            raise ValueError(
                f"{type(self)} does not support generic visit of expressions! Define handling for expression {type(expr)} explicitly!")

        def visit_Input(self, expr: Input):
            return IntervalLattice().top()

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
                raise ValueError(f"Binary Operator {expr.operator} is not supported!")

        def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation):
            r = self.visit(expr.expression)
            if expr.operator == UnaryArithmeticOperation.Operator.Add:
                return r
            elif expr.operator == UnaryArithmeticOperation.Operator.Sub:
                return r.negate()
            else:
                raise ValueError(f"Unary Operator {expr.operator} is not supported!")

        def visit_Literal(self, expr: Literal):
            if expr.typ == int:
                c = int(expr.val)
                return IntervalLattice(c, c)
            else:
                raise ValueError(f"Literal type {expr.typ} is not supported!")

    _visitor = Visitor()  # static class member shared between all instances


class IntervalStore(StoreLattice, NumericalDomain):
    def __init__(self, variables: List[VariableIdentifier]):
        super().__init__(variables, {int: IntervalLattice})
        self._visitor = IntervalStore.Visitor(self)

    def forget(self, var: VariableIdentifier):
        self.variables[var].top()

    def set_bounds(self, var: VariableIdentifier, lower: int, upper: int):
        self.variables[var].lower = lower
        self.variables[var].upper = upper

    def set_interval(self, var: VariableIdentifier, interval: IntervalLattice):
        self.variables[var].lower = interval.lower
        self.variables[var].upper = interval.upper

    def set_lb(self, var: VariableIdentifier, constant):
        self.variables[var].lower = constant

    def set_ub(self, var: VariableIdentifier, constant):
        self.variables[var].upper = constant

    def evaluate(self, expr: Expression):
        interval = self._visitor.visit(expr)
        return interval

    class Visitor(IntervalLattice.Visitor):
        """A visitor to abstractly evaluate an expression (with variables) in the interval domain."""

        def __init__(self, interval_store):
            self._store = interval_store  # keep a reference to container interval store

        @property
        def store(self):
            return self._store

        def visit_VariableIdentifier(self, expr: VariableIdentifier):
            if expr.typ == int:
                return self.store.variables[expr]
            else:
                raise ValueError(f"Variable type {expr.typ} is not supported!")


class IntervalDomain(IntervalStore, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Interval Domain (State) for given variables.

        :param variables: list of program variables
        """
        super().__init__(variables)

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'IntervalDomain':
        if isinstance(left, VariableIdentifier):
            if left.typ == int:
                self.variables[left] = self._visitor.visit(right)
        else:
            raise NotImplementedError("")
        return self

    def _assume(self, condition: Expression) -> 'IntervalDomain':
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

    def _output(self, output: Expression) -> 'IntervalDomain':
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression):
        raise NotImplementedError("")
