import unittest
import glob
import os
import ast

from abstract_domains.usage.stack import UsedStack
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from frontend.cfg_generator import CfgVisitor
from semantics.usage.usage_semantics import UsageSemantics
from visualization.graph_renderer import CfgRenderer, AnalysisResultRenderer


class UsageTestCase(unittest.TestCase):
    def __init__(self, source_path):
        super().__init__()
        self._source_path = source_path

    def runTest(self):
        name = os.path.splitext(os.path.basename(self._source_path))[0]
        print(f"Start test for Python source at {self._source_path}")

        with open(self._source_path, 'r') as source_file:
            source = source_file.read()
        root = ast.parse(source)
        cfg = CfgVisitor().visit(root)
        CfgRenderer().render(cfg, label=f"CFG for {self._source_path}", filename=f"CFG {name}", directory="graphs",
                             view=False)

        # find all variables
        variable_names = sorted(
            {node.id for node in ast.walk(root) if
             isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)})
        variables = [VariableIdentifier(int, name) for name in variable_names]

        backward_interpreter = BackwardInterpreter(cfg, UsageSemantics(), 3)
        usage_analysis = backward_interpreter.analyze(UsedStack(variables))
        AnalysisResultRenderer().render((cfg, usage_analysis), label=f"CFG with Results for {self._source_path}",
                                        filename=f"CFGR {name}", directory="graphs", view=False)


def suite():
    s = unittest.TestSuite()

    for path in glob.iglob('./usage/*.py'):
        if os.path.basename(path) != "__init__.py":
            s.addTest(UsageTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
