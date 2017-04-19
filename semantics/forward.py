from abstract_domains.state import State
from core.statements import VariableAccess, Assignment, Call
from semantics.semantics import Semantics, VariableAccessSemantics, LiteralEvaluationSemantics, BuiltInCallSemantics


class ForwardSemantics(Semantics):
    pass


class AssignmentSemantics(ForwardSemantics):

    def assignment_semantics(self, stmt: Assignment, state: State) -> State:
        lhs = self.semantics(stmt.left, state).result    # lhs evaluation
        rhs = self.semantics(stmt.right, state).result   # rhs evaluation
        if isinstance(stmt.left, VariableAccess):
            return state.assign_variable(lhs, rhs)
        else:
            raise NotImplementedError("Forward semantics for assignment {0!s} not yet implemented!".format(self))


class CustomCallSemantics(ForwardSemantics):
    def custom_call_semantics(self, stmt: Call, state: State) -> State:
        raise NotImplementedError("Forward semantics for call statement {} not yet implemented!".format(stmt))


class DefaultForwardSemantics(
    LiteralEvaluationSemantics, VariableAccessSemantics, BuiltInCallSemantics, CustomCallSemantics, AssignmentSemantics
):
    pass
