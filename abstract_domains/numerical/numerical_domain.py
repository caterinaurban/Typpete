from abc import ABCMeta

from abstract_domains.lattice import Lattice


class NumericalDomain(Lattice, metaclass=ABCMeta):
    pass
