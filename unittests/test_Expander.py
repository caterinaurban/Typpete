import unittest

from core.expressions_tools import simplify, expand
from unittests.generic_tests import ExpressionTreeTestCase


class TestExpander(ExpressionTreeTestCase):
    def __init__(self, name, source, expected_result):
        super().__init__(source, f"Expander - {name}")
        self._expected_result = expected_result

    def runTest(self):
        result = super().runTest()

        result_store = result.get_node_result(self.cfg.nodes[2])[1]
        right_expr = result_store.store[self.variables['a']]

        expanded_expr = expand(right_expr)

        self.assertEqual(str(expanded_expr), self._expected_result, self.source)


def suite():
    s = unittest.TestSuite()
    s.addTest(TestExpander("simple", """a = b + 2 + 3""", "b + 2 + 3"))
    s.addTest(TestExpander("simple", """a = c - 4 - b + 2 + 3""", "c + -(4) + -(b) + 2 + 3"))
    s.addTest(TestExpander("simple", """a = c - 10 - b + 2 + 3""", "c + -(10) + -(b) + 2 + 3"))
    s.addTest(TestExpander("simple", """a = -(c - 3) - b""", "-(c) + 3 + -(b)"))
    s.addTest(TestExpander("nested", """a = -(c - 3) * (d + 5)""", "(-(c) * d) + (-(c) * 5) + (3 * d) + (3 * 5)"))
    s.addTest(
        TestExpander("nested", """a = ((c - 3) * (d + 5))*(c)""",
                     "((c * d) * c) + ((c * 5) * c) + ((-(3) * d) * c) + ((-(3) * 5) * c)"))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
