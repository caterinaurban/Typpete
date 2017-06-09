from abstract_domains.numerical.numerical_domain import NumericalDomain


class Octagon(NumericalDomain):
    def default(self):
        self.top()

    def _less_equal(self, other: 'Octagon') -> bool:
        return all([x < y for x,y in zip(self.dbm, other.dbm)])

    def _meet(self, other: 'Octagon'):
        pass

    def _join(self, other: 'Octagon') -> 'Octagon':
        pass

    def _widening(self, other: 'Octagon'):
        pass
