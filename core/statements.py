from abc import ABCMeta, abstractmethod
from state import State


class Statement(metaclass=ABCMeta):

    def __init__(self, pp):
        """Statement representation.
        
        :param pp: program point associated with the statement  
        """
        self.pp = pp

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def forward_semantics(self, state: State) -> State:
        """Abstract forward semantics of the statement. 
        
        :param state: the state before the statement
        :return: the state after the statement
        """
        pass

    @abstractmethod
    def backward_semantics(self, state: State) -> State:
        """Abstract backwards semantics of the statement.
        
        :param state: the state after the statement
        :return: the state before the statement
        """
        pass
