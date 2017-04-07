from abc import abstractmethod
from copy import deepcopy
from expressions import Expression, Constant, VariableIdentifier
from lattice import Lattice
from typing import Set


class State(Lattice):
    class Internal(Lattice.Internal):
        def __init__(self, kind: Lattice.Kind, result: Set[Expression]):
            """Analysis state internal representation.
            
            :param kind: kind of lattice element
            :param result: set of expressions representing the result of the previously analyzed statement
            """
            super().__init__(kind)
            self._result = result

        @property
        def result(self):
            return self._result

        @result.setter
        def result(self, result: Set[Expression]):
            self._result = result

    def __init__(self, kind: Lattice.Kind = Lattice.Kind.Default, result: Set[Expression] = set()):
        """Analysis state representation. 
        Account for lattice operations and statement effects by modifying the current internal representation.
        
        :param result: set of expressions representing the result of the previously analyzed statement 
        """
        super().__init__(kind)
        self._internal = State.Internal(kind, result)

    @property
    def internal(self):
        return self._internal

    @property
    def result(self):
        return self.internal.result

    @result.setter
    def result(self, result):
        self.internal.result = result

    @abstractmethod
    def __str__(self):
        """Analysis state string representation.
        
        :return: string representing the analysis state
        """

    @abstractmethod
    def access_variable_value(self, variable: VariableIdentifier) -> Set[Expression]:
        """Retrieve a variable value. Account for side-effects by modifying the current state. 
        
        :param variable: variable to retrieve the value of
        :return: set of expressions representing the variable value
        """

    def access_variable(self, variable: VariableIdentifier) -> 'State':
        """Access a variable.
        
        :param variable: variable to be accesses
        :return: current state modified by the variable access
        """
        self.result = self.access_variable_value(variable)
        return self

    @abstractmethod
    def assign_variable_expression(self, left: Expression, right: Expression) -> 'State':
        """Assign an expression to a variable.
        
        :param left: expression representing the variable to be assigned to 
        :param right: expression representing the expression to assign
        :return: current state modified by the variable assignment
        """

    def assign_variable(self, left: Set[Expression], right: Set[Expression]) -> 'State':
        """Assign an expression to a variable.
        
        :param left: set of expressions representing the variable to be assigned to
        :param right: set of expressions representing the expression to assign
        :return: current state modified by the variable assignment
        """
        self.big_join([deepcopy(self).assign_variable_expression(lhs, rhs) for lhs in left for rhs in right])
        self.result = set()     # assignments have no result, only side-effects
        return self

    @abstractmethod
    def evaluate_constant_value(self, constant: Constant) -> Set[Expression]:
        """Retrieve a constant value. Account for side-effects by modifying the current state.
        
        :param constant: constant to retrieve the value of
        :return: set of expressions representing the constant value
        """

    def evaluate_constant(self, constant: Constant) -> 'State':
        """Evaluate a constant.
        
        :param constant: constant to be evaluated
        :return: current state modified by the constant evaluation
        """
        self.result = self.evaluate_constant_value(constant)
        return self

    @abstractmethod
    def substitute_variable_expression(self, left: Expression, right: Expression) -> 'State':
        """Substitute an expression to a variable.

        :param left: set of expressions representing the variable to be substituted
        :param right: set of expressions representing the expression to substitute
        :return: current state modified by the variable substitution
        """

    def substitute_variable(self, left: Set[Expression], right: Set[Expression]) -> 'State':
        """Substitute an expression to a variable.
        
        :param left: set of expressions representing the variable to be substituted
        :param right: set of expressions representing the expression to substitute
        :return: current state modified by the variable substitution
        """
        self.big_join([deepcopy(self).substitute_variable_expression(lhs, rhs) for lhs in left for rhs in right])
        self.result = set()  # assignments have no result, only side-effects
        return self
