import glob
import unittest
import ast
from abstract_domains.usage.stack import UsedStack
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from frontend.cfg_generator import ast_to_cfg
from semantics.usage.usage_semantics import UsageSemantics
from visualization.graph_renderer import CfgRenderer, AnalysisResultRenderer
from unittests.test_tools import *


class UsageTestCase(unittest.TestCase):
    def __init__(self, source_path):
        super().__init__()
        self._source_path = source_path

    def runTest(self):
        name = source_path_to_name(self._source_path)
        print(f"Start test for Python source at {self._source_path}")

        with open(self._source_path, 'r') as source_file:
            source = source_file.read()
        root = ast.parse(source)
        cfg = ast_to_cfg(root)
        CfgRenderer().render(cfg, label=f"CFG for {self._source_path}", filename=f"CFG {name}", directory="graphs",
                             view=False)

        # find all variables
        variable_names = sorted(
            {node.id for node in ast.walk(root) if
             isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)})
        variables = [VariableIdentifier(int, name) for name in variable_names]

        # Run Usage Analysis
        backward_interpreter = BackwardInterpreter(cfg, UsageSemantics(), 3)
        result = backward_interpreter.analyze(UsedStack(variables))
        AnalysisResultRenderer().render((cfg, result), label=f"CFG with Results for {self._source_path}",
                                        filename=f"CFGR {name}", directory="graphs", view=False)

        for line, expected_result in find_result_comments(source):
            actual_result = find_analysis_result_for_comments(cfg, result, line)
            actual_result_str = str(actual_result)
            self.assertEqual(expected_result, actual_result_str,
                             f"expected != actual result at line {line}")


def suite():
    s = unittest.TestSuite()

    for path in glob.iglob('./usage/**.py'):
        if os.path.basename(path) != "__init__.py":
            s.addTest(UsageTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
