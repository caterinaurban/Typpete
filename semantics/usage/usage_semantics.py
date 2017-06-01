from abstract_domains.state import State
from core.statements import Call
from semantics.backward import DefaultBackwardSemantics


class UsageSemantics(DefaultBackwardSemantics):
    def user_defined_call_semantics(self, stmt: Call, state: State) -> State:
        raise NotImplementedError("Usage semantics for call statement {} not yet implemented!".format(stmt))
