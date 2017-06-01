from abstract_domains.state import State
from core.expressions import BinaryArithmeticOperation, BinaryOperation, BinaryComparisonOperation, UnaryOperation, \
    UnaryArithmeticOperation, UnaryBooleanOperation, BinaryBooleanOperation, Input, ListDisplay, Slice, Index
from core.statements import Statement, VariableAccess, LiteralEvaluation, Call, ListDisplayStmt, SliceStmt, IndexStmt
from functools import reduce
import re
import itertools

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
    """Semantics of statements. Independently of the direction (forward/backward) of the analysis."""

    def semantics(self, stmt: Statement, state: State) -> State:
        """Semantics of a statement.
        
        :param stmt: statement to be executed
        :param state: state before executing the statement
        :return: state modified by the statement execution
        """
        name = '{}_semantics'.format(camel_to_snake(stmt.__class__.__name__))
        if hasattr(self, name):
            return getattr(self, name)(stmt, state)
        else:
            raise NotImplementedError(f"Semantics for statement {stmt} of type {type(stmt)} not yet implemented! "
                                      f"You must provide method {name}(...)")


class LiteralEvaluationSemantics(Semantics):
    """Semantics of literal evaluations."""

    # noinspection PyMethodMayBeStatic
    def literal_evaluation_semantics(self, stmt: LiteralEvaluation, state: State) -> State:
        """Semantics of a literal evaluation.
        
        :param stmt: literal evaluation statement to be executed
        :param state: state before executing the literal evaluation
        :return: stated modified by the literal evaluation
        """
        return state.evaluate_literal(stmt.literal)


class VariableAccessSemantics(Semantics):
    """Semantics of variable accesses."""

    # noinspection PyMethodMayBeStatic
    def variable_access_semantics(self, stmt: VariableAccess, state: State) -> State:
        """Semantics of a variable access.
        
        :param stmt: variable access statement to be executed
        :param state: state before executing the variable access
        :return: state modified by the variable access
        """
        return state.access_variable(stmt.var)


class ListSemantics(Semantics):
    """Semantics of list accesses."""

    # noinspection PyMethodMayBeStatic
    def list_display_stmt_semantics(self, stmt: ListDisplayStmt, state: State) -> State:
        """Semantics of a list display statement.

        :param stmt :list display statement to be executed
        :param state: state before executing the variable access
        :return: state modified by the variable access
        """
        item_sets = [list(self.semantics(item, state).result) for item in stmt.items]
        products = itertools.product(*item_sets)
        # TODO infer type??
        result = {ListDisplay(None, list(p)) for p in products}

        state.result = result
        return state

    # noinspection PyMethodMayBeStatic
    def slice_stmt_semantics(self, stmt: SliceStmt, state: State) -> State:
        """Semantics of a slice statement.

        :param stmt: slice statement to be executed
        :param state: state before executing the variable access
        :return: state modified by the variable access
        """
        targets = self.semantics(stmt.target, state).result
        if stmt.lower:
            lowers = self.semantics(stmt.lower, state).result
        else:
            lowers = {None}
        if stmt.step:
            steps = self.semantics(stmt.step, state).result
        else:
            steps = {None}
        if stmt.upper:
            uppers = self.semantics(stmt.upper, state).result
        else:
            uppers = {None}

        products = itertools.product(targets, lowers, steps, uppers)

        # TODO infer type of Slice??
        result = {Slice(None, target, lower, step, upper) for target, lower, step, upper in products}

        state.result = result
        return state

    # noinspection PyMethodMayBeStatic
    def index_stmt_semantics(self, stmt: IndexStmt, state: State) -> State:
        """Semantics of a index statement.

        :param stmt: index statement to be executed
        :param state: state before executing the variable access
        :return: state modified by the variable access
        """
        targets = self.semantics(stmt.target, state).result
        indices = self.semantics(stmt.index, state).result

        products = itertools.product(targets, indices)

        # TODO infer type of Slice??
        result = {Index(None, target, index) for target, index in products}

        state.result = result
        return state


class CallSemantics(Semantics):
    """Semantics of function/method calls."""

    def call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a function/method call.
        
        :param stmt: call statement to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        name = '{}_call_semantics'.format(stmt.name)
        if hasattr(self, name):
            return getattr(self, name)(stmt, state)
        else:
            return getattr(self, 'user_defined_call_semantics')(stmt, state)


class BuiltInCallSemantics(CallSemantics):
    """Semantics of built-in function/method calls."""

    def input_call_semantics(self, stmt: Call, state: State) -> State:
        state.result = {Input(stmt.typ)}
        return state

    def print_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'print'.
        
        :param stmt: call to 'print' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        argument = self.semantics(stmt.arguments[0], state).result  # argument evaluation
        return state.output(argument)

    def unary_operation(self, stmt: Call, operator: UnaryOperation.Operator, state: State) -> State:
        assert len(stmt.arguments) == 1  # unary operations have exactly one argument
        argument = self.semantics(stmt.arguments[0], state).result  # argument evaluation
        result = set()
        if isinstance(operator, UnaryArithmeticOperation.Operator):
            expression = set(UnaryArithmeticOperation(stmt.typ, operator, expr) for expr in argument)
            result = result.union(expression)
        elif isinstance(operator, UnaryBooleanOperation.Operator):
            expression = set(UnaryBooleanOperation(stmt.typ, operator, expr) for expr in argument)
            result = result.union(expression)
        else:
            raise NotImplementedError(
                f"Semantics for statement {operator} of type {type(operator)} not yet implemented!")
        state.result = result
        return state

    def not_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '!' (negation).
        
        :param stmt: call to '!' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.unary_operation(stmt, UnaryBooleanOperation.Operator.Neg, state)

    def binary_operation(self, stmt: Call, operator: BinaryOperation.Operator, state: State) -> State:
        arguments = [self.semantics(argument, state).result for argument in stmt.arguments]  # argument evaluation
        result = set()
        if isinstance(operator, BinaryArithmeticOperation.Operator):
            expression = reduce(lambda lhs, rhs: set(
                BinaryArithmeticOperation(stmt.typ, left, operator, right) for left in lhs for right in rhs
            ), arguments)
            result = result.union(expression)
        elif isinstance(operator, BinaryComparisonOperation.Operator):
            expression = reduce(lambda lhs, rhs: set(
                BinaryComparisonOperation(stmt.typ, left, operator, right) for left in lhs for right in rhs
            ), arguments)
            result = result.union(expression)
        elif isinstance(operator, BinaryBooleanOperation.Operator):
            expression = reduce(lambda lhs, rhs: set(
                BinaryBooleanOperation(stmt.typ, left, operator, right) for left in lhs for right in rhs
            ), arguments)
            result = result.union(expression)
        else:
            raise NotImplementedError(
                f"Semantics for statement {operator} of type {type(operator)} not yet implemented!")
        state.result = result
        return state

    def add_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '+' (addition, not concatenation).
        
        :param stmt: call to '+' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Add, state)

    def sub_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '-' (subtraction).
        
        :param stmt: call to '-' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Sub, state)

    def mult_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '*' (multiplication, not repetition).

        :param stmt: call to '*' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Mult, state)

    def div_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '/' (division).
        
        :param stmt: call to '/' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryArithmeticOperation.Operator.Div, state)

    def uadd_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '+X' (unary plus).

        :param stmt: call to '+' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.unary_operation(stmt, UnaryArithmeticOperation.Operator.Add, state)

    def usub_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '-X' (unary minus).

        :param stmt: call to '-' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.unary_operation(stmt, UnaryArithmeticOperation.Operator.Sub, state)

    def eq_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '==' (equality).
        
        :param stmt: call to '==' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Eq, state)

    def noteq_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '!=' (inequality).
        
        :param stmt: call to '!=' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement 
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.NotEq, state)

    def lt_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '<' (less than).
        
        :param stmt: call to '<' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Lt, state)

    def lte_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '<=' (less than or equal to).
        
        :param stmt: call to '<=' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.LtE, state)

    def gt_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '>' (greater than).
        
        :param stmt: call to '>' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Gt, state)

    def gte_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to '>=' (greater than or equal to).
        
        :param stmt: call to '>=' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement"""
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.GtE, state)

    def is_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'is' (identity).
        
        :param stmt: call to 'is' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.Is, state)

    def isnot_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'is not' (mismatch).
        
        :param stmt: call to 'is not' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.IsNot, state)

    def in_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'in' (membership).
        
        :param stmt: call to 'is' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.In, state)

    def notin_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'not in' (non-membership).
        
        :param stmt: call to 'not in' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryComparisonOperation.Operator.NotIn, state)

    def and_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'and'.

        :param stmt: call to 'add' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryBooleanOperation.Operator.And, state)

    def or_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'or'.

        :param stmt: call to 'or' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryBooleanOperation.Operator.Or, state)

    def xor_call_semantics(self, stmt: Call, state: State) -> State:
        """Semantics of a call to 'xor'.

        :param stmt: call to 'xor' to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        return self.binary_operation(stmt, BinaryBooleanOperation.Operator.Xor, state)


class DefaultSemantics(LiteralEvaluationSemantics, VariableAccessSemantics, ListSemantics, BuiltInCallSemantics):
    """Default semantics of statements. Independently of the direction (forward/backward) of the semantics."""
    pass
