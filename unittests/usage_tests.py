import io
import tokenize
import unittest
import glob
import os
import ast

import re

from abstract_domains.usage.stack import UsedStack
from core.cfg import Basic, Loop
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from frontend.cfg_generator import ast_to_cfg
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

        # Parse comments to find expected results
        pattern = re.compile('RESULT:?\s*(?P<result>.*)')
        for t in tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline):
            if t.type == tokenize.COMMENT:
                comment = t.string.strip("# ")
                m = pattern.match(comment)
                if m:
                    expected_result = m.group('result')
                    line = t.start[0]

                    # search for analysis result of a statement with the same source line
                    actual_result = None
                    for node in cfg.nodes.values():
                        states = result.get_node_result(node)

                        for i, stmt in enumerate(node.stmts):
                            if stmt.pp.line == line:
                                actual_result = states[i]
                                break

                        if actual_result:
                            break

                    if actual_result:
                        actual_result_str = str(actual_result)
                        self.assertEqual(expected_result, actual_result_str,
                                         f"expected != actual result at line {line}")
                    else:
                        raise RuntimeWarning(
                            f"No analysis result found for RESULT-comment '{comment}' at line {line}!")


def suite():
    s = unittest.TestSuite()

    for path in glob.iglob('./usage/**.py'):
        if os.path.basename(path) != "__init__.py":
            s.addTest(UsageTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
