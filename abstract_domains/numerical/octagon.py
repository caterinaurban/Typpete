from enum import IntEnum

from abstract_domains.lattice import BottomElementMixin
from abstract_domains.numerical.dbm import IntegerCDBM
from abstract_domains.numerical.numerical_domain import NumericalDomain
from abstract_domains.state import State
from core.expressions import *
from typing import List, Set, Tuple, Union
from math import inf, isinf

from core.expressions_tools import ExpressionVisitor


class VariableSign(IntEnum):
    """PLUS/MINUS sign of a variable. Used for indexing into (C)DBM"""
    # do not change values blindly, they are used for easy implementation
    PLUS = 0
    MINUS = 1


PLUS = VariableSign.PLUS
MINUS = VariableSign.MINUS


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

    def __getitem__(self, index_tuple: Tuple[VariableIdentifier, VariableSign, VariableIdentifier, VariableSign]):
        if len(index_tuple) == 4:
            var1, sign1, var2, sign2 = index_tuple
            return self.dbm[self._var_to_index[var1 + sign1], self._var_to_index[var2 + sign2]]
        else:
            raise ValueError("Index into octagon has invalid format.")

    def __setitem__(self, index: Union[Tuple[VariableIdentifier, VariableSign], Tuple[
        VariableIdentifier, VariableSign, VariableIdentifier, VariableSign]], value):
        if len(index) == 4:
            var1, sign1, var2, sign2 = index
            i, j = self._var_to_index[var1 + sign1], self._var_to_index[var2 + sign2]
            if i != j:
                self.dbm[i, j] = value
        if len(index) == 2:
            var, sign = index
            k = self._var_to_index[var + sign]
            for i in range(self.dbm.size):
                if i != k:
                    self.dbm[i, k] = value
                    self.dbm[k, i] = value
        else:
            raise ValueError("Index into octagon has invalid format.")

    def __repr__(self):
        res = []
        # represent unary constraints first
        for var in self._variables_list:
            lower = self[var, PLUS, var, MINUS] / 2
            upper = self[var, MINUS, var, PLUS] / 2
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
                    c = self[var1, MINUS, var2, PLUS]
                    if c < inf:
                        res.append(f"{var1.name}+{var2.name}<={c}")
                    c = self[var1, MINUS, var2, MINUS]
                    if c < inf:
                        res.append(f"{var1.name}-{var2.name}<={c}")
                    c = self[var1, PLUS, var2, PLUS]
                    if c < inf:
                        res.append(f"-{var1.name}+{var2.name}<={c}")
                    c = self[var1, PLUS, var2, MINUS]
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
        return all([isinf(b) for k, b in self.dbm.items() if b[0] != b[1]])  # check all inf, ignore diagonal for check

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
        self[var, PLUS] = inf
        self[var, MINUS] = inf

    def set_variable_constant(self, var: VariableIdentifier, constant):
        self.dbm[var, PLUS, var, MINUS] = -2 * constant  # encodes -2*var <= -2*constant <=> var >= constant
        self.dbm[var, MINUS, var, PLUS] = 2 * constant  # encodes 2*var <= 2*constant <=> var <= constant

    def set_expression_constant(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_variable_lb(self, var: VariableIdentifier, constant):
        self.dbm[var, MINUS, var, PLUS] = 2 * constant  # encodes 2*var <= 2*constant <=> var <= constant

    def set_variable_ub(self, var: VariableIdentifier, constant):
        self.dbm[var, PLUS, var, MINUS] = -2 * constant  # encodes -2*var <= -2*constant <=> var >= constant

    def set_expression_lb(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_expression_ub(self, expr: Expression, constant):
        raise NotImplementedError()

    def set_variable_difference_ub(self, sign1: VariableSign, var1: VariableIdentifier, sign2: VariableSign,
                                   var2: VariableIdentifier, constant):
        self.dbm[var1, MINUS, var2, MINUS] = constant  # encodes -2*var <= -2*constant <=> var >= constant
        self.dbm[var, MINUS, var, PLUS] = 2 * constant  # encodes 2*var <= 2*constant <=> var <= constant

    def set_expression_difference_ub(self, expr1: Expression, expr2: Expression, constant):
        raise NotImplementedError()


class Octagon(OctagonLattice, State):
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
