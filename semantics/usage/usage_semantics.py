from abstract_domains.state import State
from core.expressions import Value
from core.statements import Call
from semantics.backward import DefaultBackwardSemantics


class UsageSemantics(DefaultBackwardSemantics):
    def user_defined_call_semantics(self, stmt: Call, state: State) -> State:
        raise NotImplementedError("Usage semantics for call statement {} not yet implemented!".format(stmt))

    def print_call_semantics(self, stmt: Call, state: State) -> State:
        if len(stmt.arguments) != 1:
            raise NotImplementedError(f"No semantics implemented for the multiple arguments to print()")

        state.inside_print = True
        for arg in stmt.arguments:
            state = self.semantics(arg, state)

        state.inside_print = False

        return state

    def input_call_semantics(self, stmt: Call, state: State) -> State:
        if len(stmt.arguments) != 0:
            raise NotImplementedError(f"No semantics implemented for any arguments to input()")

        for arg in stmt.arguments:
            state = self.semantics(arg, state)

        state.result = {Value(str)}
        return state

    def int_call_semantics(self, stmt: Call, state: State) -> State:
        if len(stmt.arguments) != 1:
            raise NotImplementedError(f"No semantics implemented for the multiple arguments to int()")

        for arg in stmt.arguments:
            state = self.semantics(arg, state)

        state.result = {Value(int)}
        return state

    def bool_call_semantics(self, stmt: Call, state: State) -> State:
        if len(stmt.arguments) != 1:
            raise NotImplementedError(f"No semantics implemented for the multiple arguments to bool()")

        for arg in stmt.arguments:
            state = self.semantics(arg, state)

        state.result = {Value(bool)}
        return state
