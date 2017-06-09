from unittest import TestCase
from math import inf
from abstract_domains.numerical.dbm import CDBM


class TestCDBM(TestCase):
    def test_set_get(self):
        dbm = CDBM(6)
        dbm[0, 0] = 10
        self.assertEqual(dbm[0, 0], 10)
        # print(dbm)

        dbm = CDBM(6)
        dbm[1, 4] = 10
        self.assertEqual(dbm[1, 4], 10)
        # print(dbm)

        dbm = CDBM(6)
        dbm[0, 2] = 10
        self.assertEqual(dbm[0, 2], dbm[3, 1])
        # print(dbm)

        dbm = CDBM(6)
        dbm[1, 0] = 10
        self.assertNotEqual(dbm[1, 0], dbm[0, 1])
        # print(dbm)

        dbm = CDBM(6)
        dbm[4, 2] = 10
        self.assertNotEqual(dbm[4, 2], dbm[2, 4])
        # print(dbm)

        with self.assertRaises(AssertionError):
            CDBM(5)
