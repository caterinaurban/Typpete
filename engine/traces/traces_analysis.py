import ast
from abstract_domains.traces.traces_domain import TracesState
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from engine.runner import Runner
from semantics.backward import DefaultBackwardSemantics


class TracesAnalysis(Runner):

    def interpreter(self):
        return BackwardInterpreter(self.cfg, DefaultBackwardSemantics(), 3)

    def state(self):
        names = {nd.id for nd in ast.walk(self.tree) if isinstance(nd, ast.Name) and isinstance(nd.ctx, ast.Store)}
        variables = [VariableIdentifier(int, name) for name in names]
        return TracesState(variables, True)
