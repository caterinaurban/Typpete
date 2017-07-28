import ast
from abstract_domains.usage.stack import UsedStack
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from engine.runner import Runner
from semantics.usage.usage_semantics import UsageSemantics


class UsageAnalysis(Runner):

    def interpreter(self):
        return BackwardInterpreter(self.cfg, UsageSemantics(), 3)

    def state(self):
        names = {nd.id for nd in ast.walk(self.tree) if isinstance(nd, ast.Name) and isinstance(nd.ctx, ast.Store)}
        variables = [VariableIdentifier(int, name) for name in names]
        return UsedStack(variables)
