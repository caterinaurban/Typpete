from unittest import TestCase
from abstract_domains.numerical.dbm import IntegerCDBM


class TestCDBM(TestCase):
    def test_set_get(self):
        dbm = IntegerCDBM(6)
        dbm[0, 0] = 10
        self.assertEqual(dbm[0, 0], 10)
        # print(dbm)

        dbm = IntegerCDBM(6)
        dbm[1, 4] = 10
        self.assertEqual(dbm[1, 4], 10)
        # print(dbm)

        dbm = IntegerCDBM(6)
        dbm[0, 2] = 10
        self.assertEqual(dbm[0, 2], dbm[3, 1])
        # print(dbm)

        dbm = IntegerCDBM(6)
        dbm[1, 0] = 10
        self.assertNotEqual(dbm[1, 0], dbm[0, 1])
        # print(dbm)

        dbm = IntegerCDBM(6)
        dbm[4, 2] = 10
        self.assertNotEqual(dbm[4, 2], dbm[2, 4])
        # print(dbm)

        with self.assertRaises(AssertionError):
            IntegerCDBM(5)

    def test_iterators(self):
        dbm = IntegerCDBM(6)
        dbm[0, 0] = 10
        self.assertEqual(len(list(dbm.items())), 24)
        # for k, v in dbm.items():
        #     print(f"{k}: {v},")

    def test_close(self):
        dbm = IntegerCDBM(4)
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(4)
        dbm[1, 0] = 11
        dbm[1, 3] = 5
        dbm[2, 3] = 32
        dbm[3, 2] = 23
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(4)
        dbm[2, 0] = -5
        dbm[3, 1] = -23
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[0, 1] = 10
        dbm[2, 4] = 5
        dbm[3, 0] = 4
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[1, 0] = 11
        dbm[1, 3] = 5
        dbm[2, 0] = -32
        dbm[3, 0] = 23
        dbm[4, 0] = -7
        dbm[5, 0] = 7
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[1, 0] = 11
        dbm[1, 3] = 5
        dbm[2, 3] = 32
        dbm[3, 2] = 23
        dbm[4, 2] = 7
        dbm[5, 1] = 7
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[1, 0] = 11
        dbm[1, 3] = 5
        dbm[2, 3] = 32
        dbm[3, 2] = 34
        dbm[4, 2] = 7
        dbm[5, 1] = 7
        dbm[3, 3] = 33
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[0, 0] = 1
        dbm[1, 1] = 1
        dbm[2, 2] = 1
        dbm[3, 3] = 1
        dbm[4, 4] = 1
        dbm[5, 5] = 1
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)

        dbm = IntegerCDBM(6)
        dbm[4, 0] = 1
        consistent = dbm.close()
        # print(dbm)
        self.assertTrue(not consistent or dbm.tightly_closed)
