import glob
from abstract_domains.usage.stack import UsedStack
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from semantics.usage.usage_semantics import UsageSemantics
from unittests.generic_tests import *


class UsageTestCase(ResultCommentsFileTestCase):
    def __init__(self, source_path):
        super().__init__(source_path)
        self._source_path = source_path

    def runTest(self):
        print(self)
        self.render_cfg()

        # find all variables
        variable_names = sorted(
            {node.id for node in ast.walk(self.ast_root) if
             isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)})
        variables = [VariableIdentifier(int, name) for name in variable_names]

        # Run Usage Analysis
        backward_interpreter = BackwardInterpreter(self.cfg, UsageSemantics(), 3)
        result = backward_interpreter.analyze(UsedStack(variables))
        self.render_result_cfg(result)
        self.check_result_comments(result)


def suite():
    s = unittest.TestSuite()

    for path in glob.iglob('./usage/**.py'):
        if os.path.basename(path) != "__init__.py":
            s.addTest(UsageTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
