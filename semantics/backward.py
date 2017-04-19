from abstract_domains.state import State
from core.statements import VariableAccess, Assignment, Call
from semantics.semantics import Semantics, DefaultSemantics


class BackwardSemantics(Semantics):
    """Backward semantics of statements."""
    pass


class UserDefinedCallSemantics(BackwardSemantics):
    """Backward semantics of user-defined function/method calls."""

    def user_defined_call_semantics(self, stmt: Call, state: State) -> State:
        """Backward semantics of a user-defined function/method call.
        
        :param stmt: call statement to be executed
        :param state: state before executing the call statement
        :return: state modified by the call statement
        """
        raise NotImplementedError("Backward semantics for call statement {} not yet implemented!".format(stmt))


class AssignmentSemantics(BackwardSemantics):
    """Backward semantics of assignments."""

    def assignment_semantics(self, stmt: Assignment, state: State) -> State:
        """Backward semantics of an assignment. 

        :param stmt: assignment statement to be executed
        :param state: state before executing the assignment
        :return: state modified by the assignment
        """
        lhs = self.semantics(stmt.left, state).result    # lhs evaluation
        rhs = self.semantics(stmt.right, state).result   # rhs evaluation
        if isinstance(stmt.left, VariableAccess):
            return state.substitute_variable(lhs, rhs)
        else:
            raise NotImplementedError("Backward semantics for assignment {0!s} not yet implemented!".format(self))


# noinspection PyAbstractClass
class DefaultBackwardSemantics(DefaultSemantics, UserDefinedCallSemantics, AssignmentSemantics):
    """Default backward semantics of statements."""
    pass
