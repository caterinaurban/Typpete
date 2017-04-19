from abstract_domains.state import State
from core.statements import VariableAccess, Assignment, Call
from semantics.semantics import Semantics, DefaultSemantics


class ForwardSemantics(Semantics):
    """Forward semantics of statements."""
    pass


class UserDefinedCallSemantics(ForwardSemantics):
    """Forward semantics of user-defined function/method calls."""

    def user_defined_call_semantics(self, stmt: Call, state: State) -> State:
        """Forward semantics of a user-defined function/method call.

        :param stmt: call statement to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        raise NotImplementedError("Forward semantics for call statement {} not yet implemented!".format(stmt))


class AssignmentSemantics(ForwardSemantics):
    """Forward semantics of assignments."""

    def assignment_semantics(self, stmt: Assignment, state: State) -> State:
        """Forward semantics of an assignment. 
        
        :param stmt: assignment statement to be executed
        :param state: state before executing the assignment
        :return: state modified by the assignment
        """
        lhs = self.semantics(stmt.left, state).result    # lhs evaluation
        rhs = self.semantics(stmt.right, state).result   # rhs evaluation
        if isinstance(stmt.left, VariableAccess):
            return state.assign_variable(lhs, rhs)
        else:
            raise NotImplementedError("Forward semantics for assignment {0!s} not yet implemented!".format(self))


# noinspection PyAbstractClass
class DefaultForwardSemantics(DefaultSemantics, UserDefinedCallSemantics, AssignmentSemantics):
    """Default forward semantics of statements."""
    pass
