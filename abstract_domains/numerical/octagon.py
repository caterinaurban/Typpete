from abstract_domains.lattice import BottomElementMixin
from abstract_domains.numerical.dbm import IntegerCDBM
from abstract_domains.numerical.interval import IntervalLattice, IntervalStore
from abstract_domains.numerical.numerical import NumericalDomain
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from core.expressions_tools import ExpressionVisitor

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
        res = []
        # represent unary constraints first
        for var in self._variables_list:
            lower = self[PLUS, var, MINUS, var] // 2
            upper = self[MINUS, var, PLUS, var] // 2
            if lower < inf and upper < inf:
                res.append(f"{lower}<={var.name}<={upper}")
            elif lower < inf:
                res.append(f"{lower}<={var.name}")
            elif upper < inf:
                res.append(f"{var.name}<={upper}")
        # represent binary constraints second
        for var1 in self._variables_list:
            for var2 in self._variables_list:
                if var1 != var2:
                    c = self[MINUS, var1, PLUS, var2]
                    if c < inf:
                        res.append(f"{var1.name}+{var2.name}<={c}")
                    c = self[MINUS, var1, MINUS, var2]
                    if c < inf:
                        res.append(f"{var1.name}-{var2.name}<={c}")
                    c = self[PLUS, var1, PLUS, var2]
                    if c < inf:
                        res.append(f"-{var1.name}+{var2.name}<={c}")
                    c = self[PLUS, var1, MINUS, var2]
                    if c < inf:
                        res.append(f"-{var1.name}-{var2.name}<={c}")
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


class SingleVarLinearForm(ExpressionVisitor):
    """Holds an expression in linear form with a single variable: `+/- var + interval`."""

    def __init__(self, expr: Expression):
        """Initializes this instance with the single variable form of an expression.
        
        If possible, this instance holds the parts of the single variable linear form separately. If not possible to 
        construct this form, this raises a ValueError.
        """
        self._var_sign = PLUS
        self._var = None
        self._interval = None

        self.visit(expr)

    @property
    def var_sign(self):
        return self._var_sign

    @var_sign.setter
    def var_sign(self, value):
        self._var_sign = value

    @property
    def var(self):
        return self._var

    @var.setter
    def var(self, value):
        if self._var:
            raise ValueError("var set twice (is immutable)!")
        self._var = value

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        if self._interval:
            raise ValueError("interval set twice (is immutable)!")
        self._interval = value

    def __str__(self):
        return f"{str(self._var_sign)} {self._var} + {self._interval}"

    # the visit methods should by design never call other visitor methods of this visitor
    # only other visitors like the interval visitor via IntervalLattice.evaluate_expression(expr)

    def visit_Literal(self, expr: Literal):
        self.interval = IntervalLattice.evaluate_expression(expr)

    def visit_VariableIdentifier(self, expr: VariableIdentifier):
        self.var = expr

    def visit_Input(self, expr: Input):
        self.interval = IntervalLattice().top()

    def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation):
        # we have to check if binary operation can be reordered to correspond to valid format: +/- var + interval
        # first check if only right argument of binary operation can be transformed to format
        try:
            self.interval = IntervalLattice.evaluate_expression(expr.left)
        except ValueError as e:
            # it is still ok if expr.left is a single variable identifier or +/- a variable identifier
            if isinstance(expr.left, VariableIdentifier):
                self.var = expr.left
            elif isinstance(expr.left, UnaryArithmeticOperation) and isinstance(expr.left.expression,
                                                                                VariableIdentifier):
                self.var = expr.left.expression
                self.var_sign = expr.left.operator
            else:
                raise e

        # second check if right argument of binary operation can be transformed to format (respecting what left was)
        def binary_to_unary_operator(binary_operator):
            if binary_operator == BinaryArithmeticOperation.Operator.Add:
                return PLUS
            elif binary_operator == BinaryArithmeticOperation.Operator.Sub:
                return MINUS
            else:
                raise ValueError()

        try:
            self.interval = IntervalLattice.evaluate_expression(expr.right)
            if binary_to_unary_operator(expr.operator) == MINUS:
                self.interval.negate()
        except ValueError as e:
            # it is still ok if expr.right is a single variable identifier or +/- a variable identifier
            if isinstance(expr.right, VariableIdentifier):
                self.var = expr.right
                self.var_sign = binary_to_unary_operator(expr.operator)
            elif isinstance(expr.right, UnaryArithmeticOperation) and isinstance(expr.right.expression,
                                                                                 VariableIdentifier):
                self.var = expr.right.expression
                self.var_sign = Sign(
                    binary_to_unary_operator(expr.operator) * expr.right.operator)
            else:
                raise e

    def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation):
        try:
            self.interval = IntervalLattice.evaluate_expression(expr)  # let IntervalLattice handle unary operator
        except ValueError as e:
            # it is still ok if expr is a single variable identifier
            if isinstance(expr.expression, VariableIdentifier):
                self.var = expr.expression
                self.var_sign = expr.operator
            else:
                raise e

    def generic_visit(self, expr):
        raise ValueError(
            f"{type(self)} does not support generic visit of expressions! Define handling for expression {type(expr)} explicitly!")


class OctagonDomain(OctagonLattice, State):
    class OctagonVisitor(ExpressionVisitor):
        def __init__(self, octagon):
            self._octagon = octagon  # keep a reference to container octagon

        @property
        def octagon(self):
            return self._octagon

        def visit_Input(self, expr: Input):
            return OctagonLattice(self.octagon._variables_list).top()

        def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation):
            pass

    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon Lattice for given variables.

        :param variables: list of program variables
        """
        super().__init__(variables)
        self._visitor = OctagonDomain.OctagonVisitor(self)

    def _substitute_variable(self, left: Expression, right: Expression) -> 'OctagonDomain':
        raise NotImplementedError()

    def _assume(self, condition: Expression) -> 'OctagonDomain':
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
                print("right is not in single variable linear form")
                pass

        return self
