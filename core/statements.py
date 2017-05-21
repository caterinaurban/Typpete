from abc import ABCMeta, abstractmethod
from core.expressions import Literal, VariableIdentifier
from typing import List


class ProgramPoint:
    def __init__(self, line: int, column: int):
        """Program point representation.
        
        :param line: line of the program
        :param column: column of the program
        """
        self._line = line
        self._column = column

    @property
    def line(self):
        return self._line

    @property
    def column(self):
        return self._column

    def __eq__(self, other: 'ProgramPoint'):
        return (self.line, self.column) == (other.line, other.column)

    def __hash__(self):
        return hash((self.line, self.column))

    def __ne__(self, other: 'ProgramPoint'):
        return not (self == other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        """Program point string representation

        :return: string representing the program point
        """
        return "[line:{0.line}, column:{0.column}]".format(self)


"""
Statements.
https://docs.python.org/3.4/reference/simple_stmts.html
"""


class Statement(metaclass=ABCMeta):
    def __init__(self, pp: ProgramPoint):
        """Statement representation.
        
        :param pp: program point associated with the statement  
        """
        self._pp = pp

    @property
    def pp(self):
        return self._pp

    def __repr__(self):
        return str(self)

    @abstractmethod
    def __str__(self):
        """Statement string representation.
        
        :return: string representing the statement
        """


"""
Expression Statements.
https://docs.python.org/3.4/reference/simple_stmts.html#expression-statements
"""


class LiteralEvaluation(Statement):
    def __init__(self, pp: ProgramPoint, literal: Literal):
        """Literal evaluation representation.

        :param pp: program point associated with the literal evaluation
        :param literal: literal being evaluated
        """
        super().__init__(pp)
        self._literal = literal

    @property
    def literal(self):
        return self._literal

    def __str__(self):
        return "{0.literal}".format(self)


class VariableAccess(Statement):
    def __init__(self, pp: ProgramPoint, var: VariableIdentifier):
        """Variable access representation.

        :param pp: program point associated with the variable access
        :param var: variable being accessed
        """
        super().__init__(pp)
        self._var = var

    @property
    def var(self):
        return self._var

    def __str__(self):
        return "{0.var}".format(self)


class Call(Statement):
    def __init__(self, pp: ProgramPoint, name: str, arguments: List[Statement], typ):
        """Call statement representation.
        
        :param pp: program point associated with the call
        :param name: name of the function/method being called
        :param arguments: list of arguments of the call
        :param typ: return type of the call
        """
        super().__init__(pp)
        self._name = name
        self._arguments = arguments
        self._typ = typ

    @property
    def name(self):
        return self._name

    @property
    def arguments(self):
        return self._arguments

    @property
    def typ(self):
        return self._typ

    def __str__(self):
        return "{}({})".format(self.name, ", ".join("{}".format(argument) for argument in self.arguments))


"""
Assignment Statements.
https://docs.python.org/3.4/reference/simple_stmts.html#assignment-statements
"""


class Assignment(Statement):
    def __init__(self, pp: ProgramPoint, left: Statement, right: Statement):
        """Assignment statement representation.

        :param pp: program point associated with the statement
        :param left: left-hand side of the assignment
        :param right: right-hand side of the assignment
        """
        super().__init__(pp)
        self._left = left
        self._right = right

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def __str__(self):
        return "{0.pp} {0.left} = {0.right}".format(self)
