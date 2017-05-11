from unittest import TestCase
from abstract_domains.usage.used import U, S, O, N, UsedLattice
from abstract_domains.usage.used_liststart import UsedListStartLattice


class TestUsedListStartLattice(TestCase):
    def test_combine(self):
        a = UsedListStartLattice(6, 4, 0)  # UUUUSS
        b = UsedListStartLattice(0, 2, 6)  # UUOOOO
        print(a)
        print(b)
        ab = a.combine(b)
        assert list(ab.suo.values()) == [0, 2, 6]  # UUOOOO
