from abstract_domains.state import State
from core.statements import VariableAccess, Assignment, Call
from semantics.semantics import Semantics, LiteralEvaluationSemantics, VariableAccessSemantics, BuiltInCallSemantics


class BackwardSemantics(Semantics):
    pass


class CustomCallSemantics(BackwardSemantics):
    def custom_call_semantics(self, stmt: Call, state: State) -> State:
        raise NotImplementedError("Backward semantics for call statement {} not yet implemented!".format(stmt))


class AssignmentSemantics(BackwardSemantics):
    def assignment_semantics(self, stmt: Assignment, state: State) -> State:
        lhs = self.semantics(stmt.left, state).result    # lhs evaluation
        rhs = self.semantics(stmt.right, state).result   # rhs evaluation
        if isinstance(stmt.left, VariableAccess):
            return state.substitute_variable(lhs, rhs)
        else:
            raise NotImplementedError("Backward semantics for assignment {0!s} not yet implemented!".format(self))


class DefaultBackwardSemantics(
    LiteralEvaluationSemantics, VariableAccessSemantics, BuiltInCallSemantics, CustomCallSemantics, AssignmentSemantics
):
    pass
