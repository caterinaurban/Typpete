from abstract_domains.state import State
from core.statements import Call
from semantics.backward import DefaultBackwardSemantics


class UsageSemantics(DefaultBackwardSemantics):
    def print_call_semantics(self, stmt: Call, state: State) -> State:
        if len(stmt.arguments) != 1:
            raise NotImplementedError(f"No semantics implemented for the multiple arguments to print()")

        state.inside_print = True
        for arg in stmt.arguments:
            state = self.semantics(arg, state)

        state.inside_print = False

        return state
