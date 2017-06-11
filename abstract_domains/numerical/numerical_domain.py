from abc import ABCMeta

from abstract_domains.lattice import BaseLattice


class NumericalDomain(BaseLattice, metaclass=ABCMeta):
    pass
