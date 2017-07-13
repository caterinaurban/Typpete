import glob
from abstract_domains.usage.stack import UsedStack
from core.expressions import VariableIdentifier
from engine.backward import BackwardInterpreter
from semantics.usage.usage_semantics import UsageSemantics
from unittests.generic_tests import ResultCommentsFileTestCase
import unittest
import os
import logging

logging.basicConfig(level=logging.INFO, filename='unittests.log', filemode='w')


class UsageTestCase(ResultCommentsFileTestCase):
    def __init__(self, source_path):
        super().__init__(source_path)
        self._source_path = source_path

    def runTest(self):
        logging.info(self)
        self.render_cfg()

        # find all variables
        variable_names = self.find_variable_names()
        variables = []
        for name in variable_names:
            # TODO remove this name hack when type inferences work
            typ = list if name.startswith("list") else int
            variables.append(VariableIdentifier(typ, name))

        # print(list(map(str,variables)))

        # Run Usage Analysis
        backward_interpreter = BackwardInterpreter(self.cfg, UsageSemantics(), 3)
        result = backward_interpreter.analyze(UsedStack(variables))
        self.render_result_cfg(result)
        self.check_result_comments(result)


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/usage/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            s.addTest(UsageTestCase(path))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
