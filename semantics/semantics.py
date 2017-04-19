from functools import reduce

from abstract_domains.state import State
from core.expressions import BinaryArithmeticOperation, BinaryOperation, BinaryComparisonOperation
from core.statements import Statement, VariableAccess, LiteralEvaluation, Call
import re

_first1 = re.compile(r'(.)([A-Z][a-z]+)')
_all2 = re.compile('([a-z0-9])([A-Z])')


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case

    :param name: name in CamelCase 
    :return: name in snake_case
    """
    subbed = _first1.sub(r'\1_\2', name)
    return _all2.sub(r'\1_\2', subbed).lower()


class Semantics:
    def semantics(self, stmt: Statement, state: State) -> State:
        name = '{}_semantics'.format(camel_to_snake(stmt.__class__.__name__))
        if hasattr(self, name):
            return getattr(self, name)(stmt, state)
        else:
            raise NotImplementedError("Semantics for statement {} not yet implemented!".format(stmt))


class LiteralEvaluationSemantics(Semantics):
    # noinspection PyMethodMayBeStatic
    def literal_evaluation_semantics(self, stmt: LiteralEvaluation, state: State) -> State:
        return state.evaluate_literal(stmt.literal)


class VariableAccessSemantics(Semantics):
    # noinspection PyMethodMayBeStatic
    def variable_access_semantics(self, stmt: VariableAccess, state: State) -> State:
        return state.access_variable(stmt.var)


class CallSemantics(Semantics):
    def call_semantics(self, stmt: Call, state: State) -> State:
        name = '{}_call_semantics'.format(stmt.name)
        if hasattr(self, name):
            return getattr(self, name)(stmt, state)
        else:
            return getattr(self, 'custom_call_semantics')(stmt, state)


class BuiltInCallSemantics(CallSemantics):

    def binary_operation(self, stmt: Call, operator: BinaryOperation.Operator, state: State) -> State:
        arguments = [self.semantics(argument, state).result for argument in stmt.arguments]   # argument evaluation
        result = set()
        if isinstance(operator, BinaryArithmeticOperation.Operator):
            expression = reduce(
                lambda lhs, rhs: set(BinaryArithmeticOperation(stmt.typ, left, operator, right) for left in lhs for right in rhs),
                arguments
            )
            result.union(expression)
        elif isinstance(operator, BinaryComparisonOperation.Operator):
            expression = reduce(
                lambda lhs, rhs: set(BinaryComparisonOperation(stmt.typ, left, operator, right) for left in lhs for right in rhs),
                arguments
            )
            result.union(expression)
        state.result = result
        return state

    def add_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Add, state)

    def sub_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Sub, state)

    def mul_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Mul, state)

    def div_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Div, state)

    def eq_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Eq, state)

    def noteq_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.NotEq, state)

    def lt_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Lt, state)

    def lte_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.LtE, state)

    def gt_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Gt, state)

    def gte_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.GtE, state)

    def is_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Is, state)

    def isnot_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.IsNot, state)

    def in_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.In, state)

    def notin_call_semantics(self, stmt: Call, state: State) -> State:
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.NotIn, state)
