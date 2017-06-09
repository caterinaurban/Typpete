from unittest import TestCase
from abstract_domains.usage.used_liststart import UsedListStartLattice
from math import inf


class TestUsedListStartLattice(TestCase):
    def test_combine(self):
        # we assume that following test lists are 6 element long (implicit, not necessary to specify)

        a = UsedListStartLattice(6, 4, 0)  # UUUUSS
        b = UsedListStartLattice(0, 2, 6)  # UUOOOO
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [0, 2, 6])  # UUOOOO

        a = UsedListStartLattice(6, 4, 0)  # UUUUSS
        b = UsedListStartLattice(6, 2, 0)  # UUSSSS
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [6, 4, 0])  # UUUUSS

        a = UsedListStartLattice(4, 2, 0)  # UUSSNN
        b = UsedListStartLattice(0, 2, 5)  # UUOOON
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [0, 2, 5])  # UUOOON

        a = UsedListStartLattice(0, 5, 0)  # UUUUUN
        b = UsedListStartLattice(0, 2, 5)  # UUOOON
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [0, 2, 5])  # UUOOON

        # we assume that following test lists are infinite long

        a = UsedListStartLattice(inf, 2, 0)  # UUSSSS...
        b = UsedListStartLattice(0, inf, 0)  # UUUUUU...
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [0, inf, 0])  # UUUUUU...

        a = UsedListStartLattice(0, inf, 0)  # UUUUUU...
        b = UsedListStartLattice(0, 0, inf)  # OOOOOO...
        ab = a.combine(b)
        self.assertEqual(list(ab.suo.values()), [0, 0, inf])  # OOOOOO...
