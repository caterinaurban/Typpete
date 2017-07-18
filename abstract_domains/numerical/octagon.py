from copy import deepcopy
from enum import Enum
from functools import reduce

from abstract_domains.lattice import BottomMixin
from abstract_domains.numerical.dbm import IntegerCDBM
from abstract_domains.numerical.interval import IntervalLattice, IntervalDomain
from abstract_domains.numerical.numerical import NumericalMixin
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from abstract_domains.numerical.linear_forms import SingleVarLinearForm, LinearForm, InvalidFormError

from core.expressions_tools import ExpressionVisitor, ExpressionTransformer, \
    make_condition_not_free, simplify

# Shorthands
Sign = UnaryArithmeticOperation.Operator
PLUS = Sign.Add
MINUS = Sign.Sub


def _index_shift(sign: Sign):
    return 1 if sign == MINUS else 0


class OctagonLattice(BottomMixin, NumericalMixin):
    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.
        
        :param variables: list of program variables
        """
        self._variables = variables
        self._var_to_index = {}
        self._index_to_var = {}
        index = 0
        for var in self.variables:
            self._var_to_index[var] = index
            self._index_to_var[index] = var
            self._index_to_var[index + 1] = var
            index += 2
        self._dbm = IntegerCDBM(len(variables) * 2)
        super().__init__()

        for key in self.dbm.keys():
            self.dbm[key] = inf

    @property
    def variables(self):
        return self._variables

    @property
    def dbm(self):
        return self._dbm

    def __getitem__(self, index_tuple: Tuple[Sign, VariableIdentifier, Sign, VariableIdentifier]):
        if len(index_tuple) == 4:
            sign1, var1, sign2, var2 = index_tuple
            return self.dbm[
                self._var_to_index[var1] + _index_shift(sign1), self._var_to_index[var2] + _index_shift(sign2)
            ]
        else:
            raise ValueError("Index into octagon has invalid format.")

    def __setitem__(self, index_tuple: Tuple[Sign, VariableIdentifier, Sign, VariableIdentifier], value):
        if len(index_tuple) == 4:
            sign1, var1, sign2, var2 = index_tuple
            i, j = self._var_to_index[var1] + _index_shift(sign1), self._var_to_index[var2] + _index_shift(sign2)
            if i != j:
                self.dbm[i, j] = value
        else:
            raise ValueError("Index into octagon has invalid format.")

    def binary_constraints_indices(self, sign1: Sign = None, var1: VariableIdentifier = None,
                                   sign2: Sign = None, var2: VariableIdentifier = None):
        signs1 = [sign1] if sign1 else [PLUS, MINUS]
        signs2 = [sign2] if sign2 else [PLUS, MINUS]
        vars1 = [var1] if var1 else self.variables
        vars2 = [var2] if var2 else self.variables
        for var1 in vars1:
            for var2 in vars2:
                if var1 == var2:
                    # do not yield diagonal and upper right triangular matrix
                    continue
                for sign1 in signs1:
                    for sign2 in signs2:
                        yield (sign1, var1, sign2, var2)

    def __repr__(self):
        if self.is_bottom():
            return "⊥"
        elif self.is_top():
            return "⊤"
        else:
            res = []
            # represent unary constraints first
            for var in self.variables:
                lower = - self[PLUS, var, MINUS, var] // 2
                upper = self[MINUS, var, PLUS, var] // 2
                if lower < inf and upper < inf:
                    res.append(f"{lower}≤{var.name}≤{upper}")
                elif lower < inf:
                    res.append(f"{lower}≤{var.name}")
                elif upper < inf:
                    res.append(f"{var.name}≤{upper}")
            # represent binary constraints second, do not repeat identical inequalities
            for i, var1 in enumerate(self.variables):
                for j, var2 in enumerate(self.variables):
                    if i > j:
                        c = self[MINUS, var1, PLUS, var2]
                        if c < inf:
                            res.append(f"{var1.name}+{var2.name}≤{c}")
                        c = self[MINUS, var1, MINUS, var2]
                        if c < inf:
                            res.append(f"{var1.name}-{var2.name}≤{c}")
                        c = self[PLUS, var1, PLUS, var2]
                        if c < inf:
                            res.append(f"-{var1.name}+{var2.name}≤{c}")
                        c = self[PLUS, var1, MINUS, var2]
                        if c < inf:
                            res.append(f"-{var1.name}-{var2.name}≤{c}")
            return ", ".join(res)

    def close(self):
        """Closes this octagon.
        
        Closes the underlying CDBM, if possible, otherwise sets this octagon to bottom.
        :return: True, if this octagon is consistent <=> this octagon is not bottom.
        """
        consistent = self.dbm.close()
        if not consistent:
            self.bottom()
        return consistent

    def top(self):
        for key in self.dbm.keys():
            self.dbm[key] = inf
        return self

    def is_top(self) -> bool:
        return all([isinf(b) for k, b in self.dbm.items() if k[0] != k[1]])  # check all inf, ignore diagonal for check

    def _less_equal(self, other: 'OctagonLattice') -> bool:
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not compare octagons with unequal sizes!")
        return all([x <= y for x, y in zip(self.dbm.values(), other.dbm.values())])

    def _meet(self, other: 'OctagonLattice'):
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not meet octagons with unequal sizes!")
        # closure is not required for meet
        self.dbm.intersection(other.dbm)
        return self

    def _join(self, other: 'OctagonLattice') -> 'OctagonLattice':
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not join octagons with unequal sizes!")
        # closure is required to get best abstraction of join
        self.close()
        other.close()
        self.dbm.union(other.dbm)
        return self

    def _widening(self, other: 'OctagonLattice'):
        self.dbm.zip(other.dbm, lambda a, b: a if a >= b else inf)
        return self

    def forget(self, var: VariableIdentifier):
        # close first to not loose implicit constraints about other variables
        self.close()

        # forget binary constraints
        for index in self.binary_constraints_indices(sign1=None, var1=var):
            self[index] = inf

        # forget unary constraints
        self[PLUS, var, MINUS, var] = inf
        self[MINUS, var, PLUS, var] = inf

    def set_bounds(self, var: VariableIdentifier, lower: int, upper: int):
        self.set_lb(var, lower)
        self.set_ub(var, upper)

    def get_bounds(self, var: VariableIdentifier):
        return self.get_lb(var), self.get_ub(var)

    def set_interval(self, var: VariableIdentifier, interval: Union[int, IntervalLattice]):
        if isinstance(interval, IntervalLattice):
            self.set_lb(var, interval.lower)
            self.set_ub(var, interval.upper)
        else:
            self.set_lb(var, interval)
            self.set_ub(var, interval)

    def get_interval(self, var: VariableIdentifier):
        return IntervalLattice(self.get_lb(var), self.get_ub(var))

    def set_lb(self, var: VariableIdentifier, constant):
        self[PLUS, var, MINUS, var] = -2 * constant  # encodes -2*var <= -2*constant <=> var >= constant

    def raise_lb(self, var: VariableIdentifier, constant):
        self.set_lb(var, max(self.get_lb(var), constant))

    def get_lb(self, var: VariableIdentifier):
        return -self[PLUS, var, MINUS, var] / 2

    def set_ub(self, var: VariableIdentifier, constant):
        self[MINUS, var, PLUS, var] = 2 * constant  # encodes 2*var <= 2*constant <=> var <= constant

    def lower_ub(self, var: VariableIdentifier, constant):
        self.set_ub(var, min(self.get_ub(var), constant))

    def get_ub(self, var: VariableIdentifier):
        return self[MINUS, var, PLUS, var] / 2

    def set_octagonal_constraint(self, sign1: Sign, var1: VariableIdentifier,
                                 sign2: Sign,
                                 var2: VariableIdentifier, constant):
        self[Sign(sign1 * MINUS), var1, sign2, var2] = constant

    def lower_octagonal_constraint(self, sign1: Sign, var1: VariableIdentifier,
                                   sign2: Sign,
                                   var2: VariableIdentifier, constant):
        self[Sign(sign1 * MINUS), var1, sign2, var2] = min(self[Sign(sign1 * MINUS), var1, sign2, var2], constant)

    def switch_constraints(self, index1, index2):
        temp = self[index1]
        self[index1] = self[index2]
        self[index2] = temp

    def to_interval_domain(self):
        interval_store = IntervalDomain(self.variables)
        for var in self.variables:
            interval_store.set_interval(var, self.get_interval(var))
        return interval_store

    def from_interval_domain(self, interval_domain: IntervalDomain):
        assert interval_domain.variables == self.variables

        for var in self.variables:
            self.set_interval(var, interval_domain.store[var])

    def evaluate(self, expr: Expression):
        return self.to_interval_domain().evaluate(expr)


class OctagonDomain(OctagonLattice, State):
    class SmallerEqualConditionTransformer(ExpressionTransformer):
        """Transforms all conditions inside expression to format ``e <= 0``.
        """

        class ConditionSet:
            class Operator(Enum):
                MEET = 0
                JOIN = 1

            def __init__(self, conditions, operator: Operator = None):
                if isinstance(conditions, list):
                    self._conditions = conditions
                else:
                    self._conditions = [conditions]
                self._cond_to_octagon = {cond: None for cond in self._conditions}
                self.operator = operator

            @property
            def condition_to_octagon(self):
                return self._cond_to_octagon

            @property
            def conditions(self):
                return self._conditions

            @conditions.setter
            def conditions(self, conditions):
                self._conditions = conditions
                self._cond_to_octagon = {cond: None for cond in conditions}

            @property
            def octagons(self):
                return self._cond_to_octagon.values()

            def combine_conditions(self):
                assert len(self.conditions) >= 1
                assert self.operator or len(self.conditions) <= 1

                def apply(x, y):
                    if self.operator == OctagonDomain.SmallerEqualConditionTransformer.ConditionSet.Operator.MEET:
                        return x.meet(y)
                    else:
                        return x.join(y)

                return reduce(apply, self.octagons)

        def visit_BinaryComparisonOperation(self, cond: BinaryComparisonOperation, *args, **kwargs):
            condition_set = self._to_LtE_operator(cond)

            # transform conditions
            updated_conditions = []
            for cond in condition_set.conditions:
                if not isinstance(cond.right, Literal) or not cond.right.val == '0':
                    # move right side to left
                    updated_conditions.append(
                        BinaryComparisonOperation(cond.typ, \
                                                  BinaryArithmeticOperation(cond.typ, cond.left,
                                                                            BinaryArithmeticOperation.Operator.Sub,
                                                                            cond.right), cond.operator,
                                                  Literal(int, '0')))
            condition_set.conditions = updated_conditions

            return condition_set

        def generic_visit(self, expr, *args, **kwargs):
            raise ValueError(
                f"{type(self)} does not support generic visit of expressions! "
                f"Define handling for expression {type(expr)} explicitly!")

        def _to_LtE_operator(self, expr: BinaryComparisonOperation):
            # noinspection PyPep8Naming
            ConditionSet = OctagonDomain.SmallerEqualConditionTransformer.ConditionSet

            if expr.operator == BinaryComparisonOperation.Operator.LtE:
                return ConditionSet(
                    expr)  # desired operator already there
            elif expr.operator == BinaryComparisonOperation.Operator.GtE:
                return ConditionSet(
                    BinaryComparisonOperation(expr.typ, expr.right, BinaryComparisonOperation.Operator.LtE,
                                              expr.left))
            elif expr.operator == BinaryComparisonOperation.Operator.Lt:
                return ConditionSet(
                    BinaryComparisonOperation(expr.typ, \
                                              BinaryArithmeticOperation(expr.typ, expr.left,
                                                                        BinaryArithmeticOperation.Operator.Add,
                                                                        Literal(int, '1')),
                                              BinaryComparisonOperation.Operator.LtE, expr.right))
            elif expr.operator == BinaryComparisonOperation.Operator.Gt:
                return self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.right, BinaryComparisonOperation.Operator.Lt, expr.left))
            elif expr.operator == BinaryComparisonOperation.Operator.Eq:
                cs1 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.LtE, expr.right))
                cs2 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.GtE, expr.right))
                return ConditionSet([cs1.conditions[0], cs2.conditions[0]], ConditionSet.Operator.MEET)

            elif expr.operator == BinaryComparisonOperation.Operator.Eq:
                cs1 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.Lt, expr.right))
                cs2 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.Gt, expr.right))
                return ConditionSet([cs1.conditions[0], cs2.conditions[0]], ConditionSet.Operator.JOIN)

    class AssumeVisitor(ExpressionVisitor):
        """Visits an expression and recursively 'assumes' the condition tree."""

        # noinspection PyMethodMayBeStatic
        def visit_UnaryBooleanOperation(self, expr: UnaryBooleanOperation, state):
            raise ValueError("The expression should not contain any unary boolean operations like negation (Neg)!")

        def visit_BinaryBooleanOperation(self, expr: BinaryBooleanOperation, state):
            if expr.operator == BinaryBooleanOperation.Operator.And:
                return self.visit(expr.left, deepcopy(state)).meet(self.visit(expr.right, deepcopy(state)))
            elif expr.operator == BinaryBooleanOperation.Operator.Or:
                return self.visit(expr.left, deepcopy(state)).join(self.visit(expr.right, deepcopy(state)))
            else:
                raise ValueError()

        # noinspection PyMethodMayBeStatic
        def visit_BinaryComparisonOperation(self, expr: BinaryComparisonOperation, state):
            # we want the following format: e <= 0
            # if not in that format, bring it to this and use a correcting +/-1 and join/meet of multiple inequalities
            condition_set = OctagonDomain.SmallerEqualConditionTransformer().visit(expr)
            for cond in condition_set.conditions:
                state_copy = deepcopy(state)
                left_side = cond.left
                try:
                    form = LinearForm(simplify(left_side))

                    # simplify implementation by always having a valid interval part
                    interval = form.interval or IntervalLattice(0, 0)

                    if not form.var_summands:  # IMPROVEMENT: this check is not handled in paper mine-HOSC06
                        # [a,b] <= 0
                        if interval.lower > 0:
                            state_copy.bottom()
                    elif len(form.var_summands) == 1:
                        # +/- x + [a, b] <= 0
                        var, sign = list(form.var_summands.items())[0]

                        if sign == PLUS:
                            # +x + [a, b] <= 0
                            state_copy.lower_ub(var, -interval.lower)
                        elif sign == MINUS:
                            # -x + [a, b] <= 0
                            state_copy.raise_lb(var, interval.lower)
                        else:
                            raise ValueError("unknown sign")
                    elif len(form.var_summands) == 2:
                        # +/- x +/- y + [a, b] <= 0
                        items = list(form.var_summands.items())
                        var1, sign1 = items[0]
                        var2, sign2 = items[1]

                        state_copy.lower_octagonal_constraint(sign1, var1, sign2, var2, -interval.lower)
                    else:
                        raise InvalidFormError(
                            "Condition with more than two variables cannot be represented as octagonal constraints")

                except InvalidFormError:
                    # Non-octagonal constraint
                    interval_domain = state.to_interval_domain()
                    interval_domain.assume({expr})
                    new_oct = OctagonDomain(state.variables)
                    new_oct.from_interval_domain(interval_domain)
                    state.meet(new_oct)

                # finally store modified octagon copy for later combination
                condition_set.condition_to_octagon[cond] = state_copy

            return condition_set.combine_conditions()

        def generic_visit(self, expr, state):
            raise ValueError(
                f"{type(self)} does not support generic visit of expressions! "
                f"Define handling for expression {type(expr)} explicitly!")

    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.
    
        :param variables: list of program variables
        """
        super().__init__(variables)

    def _substitute_variable(self, left: Expression, right: Expression) -> 'OctagonDomain':
        raise NotImplementedError()

    def _assume(self, condition: Expression) -> 'OctagonDomain':
        not_free_condition = make_condition_not_free(condition)

        res = OctagonDomain.AssumeVisitor().visit(not_free_condition, self)
        self.replace(res)

        return self

    def exit_if(self) -> 'OctagonDomain':
        return self

    def exit_loop(self) -> 'OctagonDomain':
        return self

    def _output(self, output: Expression) -> 'OctagonDomain':
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_if(self) -> 'OctagonDomain':
        return self

    def enter_loop(self) -> 'OctagonDomain':
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_constant(self, x: VariableIdentifier, interval: IntervalLattice):
        """x = [a,b]"""
        self.forget(x)
        self.set_interval(x, interval)

    def _assign_same_var_plus_constant(self, x: VariableIdentifier, interval: IntervalLattice):
        """x = x + [a,b]"""

        # update binary constraints
        for index in self.binary_constraints_indices(sign1=PLUS, var1=x):
            self[index] -= interval.lower
        for index in self.binary_constraints_indices(sign1=MINUS, var1=x):
            self[index] += interval.lower

        # update unary constraints
        self.set_interval(x,
                          IntervalLattice(self.get_lb(x) + interval.lower,
                                          self.get_ub(x) + interval.upper))

    def _assign_other_var(self, x: VariableIdentifier, y: VariableIdentifier):
        """x = y"""
        self.forget(x)
        self.set_octagonal_constraint(PLUS, x, MINUS, y, 0)
        self.set_octagonal_constraint(MINUS, x, PLUS, y, 0)

    def _assign_other_var_plus_constant(self, x: VariableIdentifier, y: VariableIdentifier, interval: IntervalLattice):
        """x = y + [a,b]"""
        self.forget(x)
        self.set_octagonal_constraint(PLUS, x, MINUS, y, interval.lower)
        self.set_octagonal_constraint(MINUS, x, PLUS, y, -interval.upper)

    def _assign_negated_same_var(self, x: VariableIdentifier):
        """x = - x"""
        # update binary constraints
        # loop through row of x
        for _, _, sign2, var2 in self.binary_constraints_indices(sign1=PLUS, var1=x):
            self.switch_constraints((PLUS, x, sign2, var2), (MINUS, x, sign2, var2))
        # loop through column of x
        for sign1, var1, _, _ in self.binary_constraints_indices(sign2=PLUS, var2=x):
            self.switch_constraints((sign1, var1, PLUS, x), (sign1, var1, MINUS, x))

        # update unary constraints
        # switch bounds via temp variable
        self.switch_constraints((PLUS, x, MINUS, x),
                                (MINUS, x, PLUS, x))

    def _assign_negated_other_var(self, x: VariableIdentifier, y: VariableIdentifier):
        """x = - y"""
        self._assign_other_var(x, y)
        self._assign_negated_same_var(x)

    def _assign_negated_same_var_plus_constant(self, x: VariableIdentifier,
                                               interval: IntervalLattice):
        """x = - x + [a,b]"""
        self._assign_negated_same_var(x)
        self._assign_same_var_plus_constant(x, interval)

    def _assign_negated_other_var_plus_constant(self, x: VariableIdentifier, y: VariableIdentifier,
                                                interval: IntervalLattice):
        """x = - y + [a,b]"""
        self._assign_negated_other_var(x, y)
        self._assign_same_var_plus_constant(x, interval)

    def _assign_variable(self, left: Expression, right: Expression) -> 'OctagonDomain':
        # Octagonal Assignments
        if isinstance(left, VariableIdentifier):
            if left.typ == int:
                try:
                    form = SingleVarLinearForm(right)
                    if not form.var and form.interval:
                        # x = [a,b]
                        self._assign_constant(left, form.interval)
                    elif form.var and form.interval:
                        # x = +/- y + [a, b]
                        if form.var == left:
                            if form.var_sign == PLUS:
                                # x = x + [a,b]
                                self._assign_same_var_plus_constant(form.var, form.interval)
                            elif form.var_sign == MINUS:
                                # x = - x + [a,b]
                                self._assign_negated_same_var_plus_constant(form.var, form.interval)
                            else:
                                raise ValueError()
                        else:
                            if form.var_sign == PLUS:
                                # x = y + [a,b]
                                self._assign_other_var_plus_constant(left, form.var, form.interval)
                    elif form.var:
                        # x = +/- x/y
                        if form.var == left:
                            if form.var_sign == PLUS:
                                pass  # nothing to change
                            elif form.var_sign == MINUS:
                                # x = - x
                                self._assign_negated_same_var(form.var)
                            else:
                                raise ValueError()
                        else:
                            # x = - y
                            self._assign_negated_other_var(left, form.var)
                    else:
                        raise ValueError()
                except InvalidFormError:
                    # right is not in single variable linear form, use interval abstraction fallback
                    interval_domain = self.to_interval_domain()
                    interval = interval_domain.evaluate(right)
                    self._assign_constant(left, interval)

        return self
