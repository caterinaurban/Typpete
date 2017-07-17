import unittest

from core.expressions_tools import simplify
from unittests.generic_tests import ExpressionTreeTestCase


class TestSimplifier(ExpressionTreeTestCase):
    def __init__(self, name, source, expected_result):
        super().__init__(source, f"SingleVarLinearForm - {name}")
        self._expected_result = expected_result

    def runTest(self):
        result = super().runTest()

        result_store = result.get_node_result(self.cfg.nodes[2])[1]
        right_expr = result_store.store[self.variables['a']]

        simplified_expr = simplify(right_expr)

        self.assertEqual(str(simplified_expr), self._expected_result, self.source)


def suite():
    s = unittest.TestSuite()
    s.addTest(TestSimplifier("simple", """a = b + 2 + 3""", "b + 5"))
    s.addTest(TestSimplifier("simple", """a = c - 4 - b + 2 + 3""", "(c + (-b)) + 1"))
    s.addTest(TestSimplifier("simple", """a = c - 10 - b + 2 + 3""", "(c + (-b)) - 5"))
    s.addTest(TestSimplifier("simple", """a = -(c - 3) - b""", "((-c) + (-b)) + 3"))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
