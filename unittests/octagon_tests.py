import glob

from abstract_domains.numerical.octagon import OctagonDomain
from core.expressions import VariableIdentifier
from engine.forward import ForwardInterpreter
from semantics.forward import DefaultForwardSemantics
from unittests.generic_tests import ResultCommentsFileTestCase
import unittest
import ast
import os
import logging

logging.basicConfig(level=logging.INFO, filename='unittests.log', filemode='w')


class OctagonTestCase(ResultCommentsFileTestCase):
    def __init__(self, source_path):
        super().__init__(source_path)
        self._source_path = source_path

    def runTest(self):
        logging.info(self)
        self.render_cfg()

        variable_names = self.find_variable_names()
        variables = []
        for name in variable_names:
            variables.append(VariableIdentifier(int, name))

        # print(list(map(str,variables)))

        # Run Octagon numerical Analysis
        forward_interpreter = ForwardInterpreter(self.cfg, DefaultForwardSemantics(), 3)
        result = forward_interpreter.analyze(OctagonDomain(variables))
        self.render_result_cfg(result)
        self.check_result_comments(result)


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/octagon/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            s.addTest(OctagonTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
