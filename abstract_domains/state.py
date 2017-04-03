from abc import ABCMeta, abstractmethod

class State(metaclass=ABCMeta):
    """Analysis state representation."""

    @abstractmethod
    def __str__(self):
        pass

    pass
