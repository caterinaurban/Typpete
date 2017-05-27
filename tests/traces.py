import ast

from abstract_domains.liveness.livedead import LiveDead
import core.expressions
from abstract_domains.traces.traces import Traces
from abstract_domains.usage.stack import UsedStack
from engine.backward import BackwardInterpreter
from frontend.cfg_generator import ast_to_cfg
from semantics.backward import DefaultBackwardSemantics
from semantics.usage.usage_semantics import UsageSemantics
from visualization.graph_renderer import AnalysisResultRenderer

# Traces
print("\nTrace\n")

file = open("traces/example.py")
tree = ast.parse(file.read())
cfg = ast_to_cfg(tree)

# find all variables
variable_names = sorted(
    {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
)
variables = [core.expressions.VariableIdentifier(int, name) for name in variable_names]

backward_interpreter = BackwardInterpreter(cfg, DefaultBackwardSemantics(), 3)
liveness_analysis = backward_interpreter.analyze(Traces(variables, True))
AnalysisResultRenderer().render((cfg, liveness_analysis), label=__file__)

#backward_interpreter = BackwardInterpreter(cfg, UsageSemantics(), 3)
#usage_analysis = backward_interpreter.analyze(UsedStack(variables))
#AnalysisResultRenderer().render((cfg, usage_analysis), label=__file__)