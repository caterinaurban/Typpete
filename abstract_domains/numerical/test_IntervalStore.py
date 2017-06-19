import unittest

from abstract_domains.numerical.interval import IntervalStore
from unittests.generic_tests import ExpressionTreeTestCase


class TestIntervalStore(ExpressionTreeTestCase):
    def __init__(self, name, source, expected_result):
        super().__init__(source, f"IntervalStore- {name}")
        self._expected_result = expected_result

    def runTest(self):
        result = super().runTest()

        result_store = result.get_node_result(self.cfg.nodes[2])[1]
        right_expr = result_store.variables[self.variables['a']]
        # print(right_expr)

        store = IntervalStore(list(self.variables.values()))
        interval = store.evaluate(right_expr)
        # print(interval)

        self.assertEqual(str(interval), self._expected_result)


def suite():
    s = unittest.TestSuite()
    s.addTest(TestIntervalStore("simple", """a = 3 * (2+5)""", "[21,21]"))
    s.addTest(TestIntervalStore("simple", """a = (3+3) * (2+5)""", "[42,42]"))
    s.addTest(TestIntervalStore("simple", """a = 3 - (2+5)""", "[-4,-4]"))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
