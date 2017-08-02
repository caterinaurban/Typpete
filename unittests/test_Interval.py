import unittest

from abstract_domains.numerical.interval_domain import Interval


class TestInterval(unittest.TestCase):
    # noinspection PyUnusedLocal
    def runTest(self):
        self.assertTrue(Interval(0, 2) < Interval(3, 4))
        self.assertTrue(Interval(0, 2) <= Interval(2, 5))
        self.assertTrue(Interval(0, 2) > Interval(-1, -1))
        with self.assertRaises(NotImplementedError):
            b = Interval(0, -1) < Interval(3, 4)
        self.assertTrue(Interval(0, -1), Interval(0, -3))

        self.assertFalse(Interval(0, 2) < Interval(1, 4))
        self.assertFalse(Interval(0, 2) < Interval(2, 4))
        self.assertFalse(Interval(0, 2) < Interval(-3, 1))
        self.assertFalse(Interval(0, 2) < Interval(-3, -2))
        self.assertFalse(Interval(0, 2) <= Interval(1, 4))


def suite():
    s = unittest.TestSuite()
    s.addTest(TestInterval())
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
