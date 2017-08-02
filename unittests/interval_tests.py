import glob

from abstract_domains.numerical.interval_domain import IntervalDomain
from core.expressions import VariableIdentifier
from engine.forward import ForwardInterpreter
from semantics.forward import DefaultForwardSemantics
from unittests.generic_tests import ResultCommentsFileTestCase
import unittest
import ast
import os
import logging

logging.basicConfig(level=logging.INFO, filename='unittests.log', filemode='w')


class IntervalTestCase(ResultCommentsFileTestCase):
    def __init__(self, source_path):
        super().__init__(source_path)
        self._source_path = source_path

    def runTest(self):
        logging.info(self)
        self.render_cfg()

        # find all variables
        variable_names = sorted(
            {node.id for node in ast.walk(self.ast_root) if
             isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)})
        variables = []
        for name in variable_names:
            variables.append(VariableIdentifier(int, name))

        # print(list(map(str,variables)))

        # Run Interval numerical Analysis
        forward_interpreter = ForwardInterpreter(self.cfg, DefaultForwardSemantics(), 3)
        result = forward_interpreter.analyze(IntervalDomain(variables))
        self.render_result_cfg(result)
        self.check_result_comments(result)


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/interval/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            s.addTest(IntervalTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
