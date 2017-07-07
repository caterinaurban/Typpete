from copy import deepcopy
from functools import reduce

from abstract_domains.lattice import BottomElementMixin, Kind
from abstract_domains.numerical.dbm import IntegerCDBM
from abstract_domains.numerical.interval import IntervalLattice, IntervalStore
from abstract_domains.numerical.numerical import NumericalDomain
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from abstract_domains.numerical.linear_forms import SingleVarLinearForm

from core.expressions_tools import ExpressionVisitor, ExpressionTransformer

Sign = UnaryArithmeticOperation.Operator
PLUS = Sign.Add
MINUS = Sign.Sub


def _index_shift(sign: Sign):
    return 1 if sign == MINUS else 0


class OctagonLattice(BottomElementMixin, NumericalDomain):
    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.
        
        :param variables: list of program variables
        """
        self._variables_list = variables
        self._var_to_index = {}
        self._index_to_var = {}
        index = 0
        for var in self._variables_list:
            self._var_to_index[var] = index
            self._index_to_var[index] = var
            self._index_to_var[index + 1] = var
            index += 2
        self._dbm = IntegerCDBM(len(variables) * 2)
        super().__init__()

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
        vars1 = [var1] if var1 else self._variables_list
        vars2 = [var2] if var2 else self._variables_list
        for var1 in vars1:
            for var2 in vars2:
                if var1 == var2:
                    # do not yield diagonal and upper right triangular matrix
                    break
                for sign1 in signs1:
                    for sign2 in signs2:
                        yield (sign1, var1, sign2, var2)

    def __repr__(self):
        if self.is_bottom():
            return "BOTTOM"
        elif self.is_top():
            return "TOP"
        else:
            res = []
            # represent unary constraints first
            for var in self._variables_list:
                lower = - self[PLUS, var, MINUS, var] // 2
                upper = self[MINUS, var, PLUS, var] // 2
                if lower < inf and upper < inf:
                    res.append(f"{lower}≤{var.name}≤{upper}")
                elif lower < inf:
                    res.append(f"{lower}≤{var.name}")
                elif upper < inf:
                    res.append(f"{var.name}≤{upper}")
            # represent binary constraints second
            for var1 in self._variables_list:
                for var2 in self._variables_list:
                    if var1 != var2:
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

    def default(self):
        self.top()
        return self

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
        self.dbm.close()
        other.dbm.close()
        self.dbm.union(other.dbm)
        return self

    def _widening(self, other: 'OctagonLattice'):
        self.dbm.zip(other.dbm, lambda a, b: a if a >= b else inf)
        return self

    def forget(self, var: VariableIdentifier):
        self.dbm.close()
        for index in self.binary_constraints_indices(sign1=None, var1=var):
            self[index] = inf

    def set_interval(self, var: VariableIdentifier, interval: Union[int, IntervalLattice]):
        if isinstance(interval, IntervalLattice):
            self.set_lb(var, interval.lower)
            self.set_ub(var, interval.upper)
        else:
            self.set_lb(var, interval)
            self.set_ub(var, interval)

    def get_interval(self, var: VariableIdentifier):
        return IntervalLattice(self.get_lb(var), self.get_ub())

    def set_lb(self, var: VariableIdentifier, constant):
        self[MINUS, var, PLUS, var] = 2 * constant  # encodes 2*var <= 2*constant <=> var <= constant

    def get_lb(self, var: VariableIdentifier):
        return self[PLUS, var, MINUS, var] / 2

    def set_ub(self, var: VariableIdentifier, constant):
        self[PLUS, var, MINUS, var] = -2 * constant  # encodes -2*var <= -2*constant <=> var >= constant

    def get_ub(self, var: VariableIdentifier):
        return self[MINUS, var, PLUS, var] / 2

    def set_octagonal_constraint(self, sign1: Sign, var1: VariableIdentifier,
                                 sign2: Sign,
                                 var2: VariableIdentifier, constant):
        self[Sign(sign1 * MINUS), var1, sign2, var2] = constant

    def switch_constraints(self, index1, index2):
        temp = self[index1]
        self[index1] = self[index2]
        self[index2] = temp

    def evaluate(self, expr: Expression):
        interval = self._visitor.visit(expr)
        return interval



class OctagonDomain(OctagonLattice, State):
    class NotFreeConditionTransformer(ExpressionTransformer):
        """Transforms an expression by pushing ``not``-operators down the expression tree and reversing binary operations
        
        Uses De-Morgans law to push down ``not``-operators. Finally gets rid of all ``not``-operators, by reversing 
        binary comparision operators that are negated. 
        """

        def visit_UnaryBooleanOperation(self, expr: UnaryBooleanOperation, invert=False):
            if expr.operator == UnaryBooleanOperation.Operator.Neg:
                return self.generic_visit(expr.expression, invert=not invert)  # double inversion cancels itself
            else:
                raise NotImplementedError()

        def visit_BinaryBooleanOperation(self, expr: BinaryBooleanOperation, invert=False):
            if invert:
                if expr.operator == BinaryBooleanOperation.Operator.And:
                    return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left, invert=True),
                                                  BinaryBooleanOperation.Operator.Or,
                                                  self.generic_visit(expr.right, invert=True))
                elif expr.operator == BinaryBooleanOperation.Operator.Or:
                    return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left, invert=True),
                                                  BinaryBooleanOperation.Operator.And,
                                                  self.generic_visit(expr.right, invert=True))
                elif expr.operator == BinaryBooleanOperation.Operator.Xor:
                    # use not(a xor b) == (a and b) or (not(a) and not(b))
                    cond_both = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=False),
                                                       BinaryBooleanOperation.Operator.And,
                                                       self.generic_visit(deepcopy(expr.right), invert=False))
                    cond_none = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=True),
                                                       BinaryBooleanOperation.Operator.And,
                                                       self.generic_visit(deepcopy(expr.right), invert=True))
                    return BinaryBooleanOperation(expr.typ, cond_both,
                                                  BinaryBooleanOperation.Operator.Or,
                                                  cond_none)
            else:
                # get rid of xor also if not inverted!
                if expr.operator == BinaryBooleanOperation.Operator.Xor:
                    # use a xor b == (a or b) and not(a and b) == (a or b) and (not(a) or not(b))
                    cond_one = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=False),
                                                      BinaryBooleanOperation.Operator.Or,
                                                      self.generic_visit(deepcopy(expr.right), invert=False))
                    cond_not_both = BinaryBooleanOperation(expr.typ,
                                                           self.generic_visit(deepcopy(expr.left), invert=True),
                                                           BinaryBooleanOperation.Operator.Or,
                                                           self.generic_visit(deepcopy(expr.right), invert=True))
                    return BinaryBooleanOperation(expr.typ, cond_one, BinaryBooleanOperation.Operator.And,
                                                  cond_not_both)
                else:
                    return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left),
                                                  expr.operator,
                                                  self.generic_visit(expr.right))

        def visit_BinaryComparisionOperation(self, expr: BinaryComparisonOperation, invert=False):
            return BinaryComparisonOperation(expr.typ, self.generic_visit(expr.left),
                                             expr.operator.reverse_operator() if invert else expr.operator,
                                             self.generic_visit(expr.right))

    class SmallerEqualConditionTransformer(ExpressionTransformer):
        """Transforms all conditions inside expression to format ``e <= 0``.
        """

        class ConditionSet:
            class Operator(Enum):
                MEET = 0
                JOIN = 1

            def __init__(self, exprs, operator: Operator = None):
                self.exprs = list(exprs)
                self.operator = operator

            def evaluate(self):
                assert self.operator or len(self.exprs) == 0

                def apply(x, y):
                    if self.operator == OctagonDomain.SmallerEqualConditionTransformer.ConditionSet.Operator.MEET:
                        return x.meet(y)
                    else:
                        return x.join(y)

                return reduce(apply, self.exprs)

        def visit_BinaryComparisionOperation(self, expr: BinaryComparisonOperation):
            condition_set = self._to_LtE_operator(expr)
            updated_condition_set = OctagonDomain.SmallerEqualConditionTransformer.ConditionSet([],
                                                                                                condition_set.operator)
            for expr in condition_set.exprs:
                if not isinstance(expr.right, Literal) or not expr.right.val == '0':
                    # move right side to left
                    updated_condition_set.exprs.append(
                        BinaryComparisonOperation(expr.typ, BinaryArithmeticOperation(expr.typ, expr.left,
                                                                                      BinaryArithmeticOperation.Operator.Sub,
                                                                                      expr.right), expr.operator,
                                                  Literal(int, '0')))
            return updated_condition_set

        def _to_LtE_operator(self, expr: BinaryComparisonOperation):
            if expr.operator == BinaryComparisonOperation.Operator.LtE:
                return OctagonDomain.SmallerEqualConditionTransformer.ConditionSet(
                    expr)  # desired operator already there
            elif expr.operator == BinaryComparisonOperation.Operator.GtE:
                return OctagonDomain.SmallerEqualConditionTransformer.ConditionSet(
                    BinaryComparisonOperation(expr.typ, expr.right, BinaryComparisonOperation.Operator.LtE,
                                              expr.left))
            elif expr.operator == BinaryComparisonOperation.Operator.Lt:
                return OctagonDomain.SmallerEqualConditionTransformer.ConditionSet(
                    BinaryComparisonOperation(expr.typ, BinaryArithmeticOperation(expr.typ, expr.left,
                                                                                  BinaryArithmeticOperation.Operator.Add,
                                                                                  Literal(int, '1')), expr.right))
            elif expr.operator == BinaryComparisonOperation.Operator.Gt:
                return self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.right, BinaryComparisonOperation.Operator.Lt, expr.left))
            elif expr.operator == BinaryComparisonOperation.Operator.Eq:
                expr1 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.LtE))
                expr2 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.GtE))
                return expr1, OctagonDomain.SmallerEqualConditionTransformer.ConditionSet.Operator.MEET, expr2
            elif expr.operator == BinaryComparisonOperation.Operator.Eq:
                oct1 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.Lt))
                oct2 = self._to_LtE_operator(
                    BinaryComparisonOperation(expr.typ, expr.left, BinaryComparisonOperation.Operator.Gt))
                return oct1, OctagonDomain.SmallerEqualConditionTransformer.ConditionSet.Operator.JOIN, oct2

    class AssumeVisitor(ExpressionVisitor):
        """Visits an expression and recursively 'assumes' the condition tree."""

        def visit(self, expr, state):
            super().visit(expr, state)

        def visit_UnaryBooleanOperation(self, expr: UnaryBooleanOperation, state):
            raise ValueError("The expression should not contain any unary boolean operations like negation (Neg)!")

        def visit_BinaryBooleanOperation(self, expr: BinaryBooleanOperation, state):
            if expr.operator == BinaryBooleanOperation.Operator.And:
                self.visit(expr.left, deepcopy(state)).meet(self.visit(expr.right, deepcopy(state)))
            elif expr.operator == BinaryBooleanOperation.Operator.Or:
                self.visit(expr.left, deepcopy(state)).join(self.visit(expr.right, deepcopy(state)))
            else:
                raise ValueError()

        def visit_BinaryComparisionOperation(self, expr: BinaryComparisonOperation):
            # we want the following format: e <= 0
            # if not in that format, bring it to this and use a correcting +/-1 and join/meet of multiple inequalities
            condition_set = OctagonDomain.SmallerEqualConditionTransformer().visit(expr)
            for cond in condition_set.exprs:
                try:
                    form = SingleVarLinearForm(cond)
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
                except ValueError:
                    # right is not in single variable linear form
                    raise NotImplementedError(
                        "right is not in single variable linear form and this is not yet supported")

    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.
    
        :param variables: list of program variables
        """
        super().__init__(variables)

    def _substitute_variable(self, left: Expression, right: Expression) -> 'OctagonDomain':
        raise NotImplementedError()

    def _assume(self, condition: Expression) -> 'OctagonDomain':
        not_free_condition = OctagonDomain.NotFreeConditionTransformer().visit(condition)

        OctagonDomain.AssumeVisitor().visit(not_free_condition)

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
        for index in self.binary_constraints_indices(sign2=PLUS, var2=x):
            self[index] += interval.lower
        for index in self.binary_constraints_indices(sign2=MINUS, var2=x):
            self[index] -= interval.lower

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
            if left.typ != int:
                raise ValueError()

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
            except ValueError:
                # right is not in single variable linear form
                raise NotImplementedError("right is not in single variable linear form and this is not yet supported")

        return self
