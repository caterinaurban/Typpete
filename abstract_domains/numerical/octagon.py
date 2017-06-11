from abstract_domains.lattice import BottomElementMixin
from abstract_domains.numerical.dbm import CDBM
from abstract_domains.numerical.numerical_domain import NumericalDomain
from core.expressions import VariableIdentifier
from typing import List
from math import inf, isinf


class Octagon(BottomElementMixin, NumericalDomain):
    def __init__(self, variables: List[VariableIdentifier]):
        """Create an Octagon for given variables.
        
        :param variables: list of program variables
        """
        super().__init__()
        self._variables_list = variables
        self._dbm = CDBM(len(variables) * 2)

    @property
    def dbm(self):
        return self._dbm

    def default(self):
        self.top()

    def top(self):
        for key in self.dbm.keys():
            self.dbm[key] = inf

    def is_top(self) -> bool:
        return all([isinf(b) for b in self.dbm.values()])

    def _less_equal(self, other: 'Octagon') -> bool:
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not compare octagons with unequal sizes!")
        return all([x <= y for x, y in zip(self.dbm.values(), other.dbm.values())])

    def _meet(self, other: 'Octagon'):
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not meet octagons with unequal sizes!")
        for key in self.dbm.keys():
            self.dbm[key] = min(self.dbm[key], other.dbm[key])

        return self

    def _join(self, other: 'Octagon') -> 'Octagon':
        if self.dbm.size != other.dbm.size:
            raise ValueError("Can not join octagons with unequal sizes!")
        for key in self.dbm.keys():
            self.dbm[key] = max(self.dbm[key], other.dbm[key])

    def _widening(self, other: 'Octagon'):
        raise NotImplementedError()
