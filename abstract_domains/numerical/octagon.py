from abstract_domains.numerical.numerical_domain import NumericalDomain


class Octagon(NumericalDomain):
    def default(self):
        self.top()

    def _less_equal(self, other: 'BaseLattice') -> bool:
        pass

    def _meet(self, other: 'BaseLattice'):
        pass

    def _join(self, other: 'BaseLattice') -> 'BaseLattice':
        pass

    def _widening(self, other: 'BaseLattice'):
        pass
