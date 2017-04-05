from abc import ABC, abstractmethod
from state import State
from expressions import Constant, VariableIdentifier


class ProgramPoint(object):
    def __init__(self, line: int, column: int):
        """Program point representation.
        
        :param line: line of the program
        :param column: column of the program
        """
        self.line = line
        self.column = column

    def __str__(self):
        """Program point string representation

        :return: string representing the program point
        """
        return "<line:{0.line}, column:{0.column}>".format(self)


class Statement(ABC):
    def __init__(self, pp: ProgramPoint):
        """Statement representation.
        
        :param pp: program point associated with the statement  
        """
        self.pp = pp

    @abstractmethod
    def __str__(self):
        """Statement string representation
        
        :return: string representing the statement
        """

    @abstractmethod
    def forward_semantics(self, state: State) -> State:
        """Abstract forward semantics of the statement. 
        
        :param state: state before the statement
        :return: state after the statement
        """

    @abstractmethod
    def backward_semantics(self, state: State) -> State:
        """Abstract backward semantics of the statement.
        
        :param state: state after the statement
        :return: state before the statement
        """


class ConstantEvaluation(Statement):
    def __init__(self, pp: ProgramPoint, val: Constant):
        """Constant evaluation representation.

        :param pp: program point associated with the constant evaluation
        :param val: constant being evaluated
        """
        super().__init__(pp)
        self.val = val

    def __str__(self):
        return str(self.val)

    def semantic(self, state: State) -> State:
        return state.evaluate_constant(self.val)

    def forward_semantics(self, state: State) -> State:
        return self.semantic(state)

    def backward_semantics(self, state: State) -> State:
        return self.semantic(state)


class VariableAccess(Statement):
    def __init__(self, pp: ProgramPoint, var: VariableIdentifier):
        """Variable access representation.
        
        :param pp: program point associated with the variable access
        :param var: variable being accessed
        """
        super().__init__(pp)
        self.var = var

    def __str__(self):
        return str(self.var)

    def semantics(self, state: State) -> State:
        return state.access_variable(self.var)

    def forward_semantics(self, state: State) -> State:
        return self.semantics(state)

    def backward_semantics(self, state: State) -> State:
        return self.semantics(state)


class Assignment(Statement):
    def __init__(self, pp: ProgramPoint, left: Statement, right: Statement):
        """Assignment statement representation.

        :param pp: program point associated with the statement
        :param left: left-hand side of the assignment
        :param right: right-hand side of the assignment
        """
        super().__init__(pp)
        self.left = left
        self.right = right

    def __str__(self):
        return "{0.left} = {0.right}".format(self)

    def forward_semantics(self, state: State) -> State:
        lhs = self.left.forward_semantics(state)  # lhs evaluation
        rhs = self.right.forward_semantics(lhs)  # rhs evaluation
        if isinstance(self.left, VariableAccess):
            return rhs.assign_variable(lhs.expression, rhs.expression)
        else:
            NotImplementedError("Forward semantics for assignment {0!s} not yet implemented!".format(self))

    def backward_semantics(self, state: State) -> State:
        lhs = self.left.backward_semantics(state)  # lhs evaluation
        rhs = self.right.backward_semantics(lhs)  # rhs evaluation
        if isinstance(self.left, VariableAccess):
            return rhs.substitute_variable(lhs.expression, rhs.expression)
        else:
            NotImplementedError("Backward semantics for assignment {0!s} not yet implemented!".format(self))
