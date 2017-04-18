from abc import abstractmethod
from abstract_domains.lattice import Lattice
from copy import deepcopy
from core.expressions import Expression, VariableIdentifier
from typing import Set


class State(Lattice):
    class Internal(Lattice.Internal):
        def __init__(self, kind: Lattice.Kind):
            """Analysis state internal representation.
            
            :param kind: kind of lattice element
            """
            super().__init__(kind)
            self._result = set()    # set of expressions representing the result of the previously analyze statement

        @property
        def result(self):
            return self._result

        @result.setter
        def result(self, result: Set[Expression]):
            self._result = result

    def __init__(self, kind: Lattice.Kind = Lattice.Kind.Default):
        """Analysis state representation. 
        Account for lattice operations and statement effects by modifying the current internal representation.
        """
        super().__init__(kind)
        self._internal = State.Internal(kind)

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
    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        """Retrieve a variable value. Account for side-effects by modifying the current state. 
        
        :param variable: variable to retrieve the value of
        :return: set of expressions representing the variable value
        """

    def access_variable(self, variable: VariableIdentifier) -> 'State':
        """Access a variable.
        
        :param variable: variable to be accesses
        :return: current state modified by the variable access
        """
        self.result = self._access_variable(variable)
        return self

    @abstractmethod
    def _assign_variable(self, left: Expression, right: Expression) -> 'State':
        """Assign an expression to a variable.
        
        :param left: expression representing the variable to be assigned to 
        :param right: expression to assign
        :return: current state modified by the variable assignment
        """

    def assign_variable(self, left: Set[Expression], right: Set[Expression]) -> 'State':
        """Assign an expression to a variable.
        
        :param left: set of expressions representing the variable to be assigned to
        :param right: set of expressions representing the expression to assign
        :return: current state modified by the variable assignment
        """
        self.big_join([deepcopy(self)._assign_variable(lhs, rhs) for lhs in left for rhs in right])
        self.result = set()     # assignments have no result, only side-effects
        return self

    @abstractmethod
    def _assume(self, condition: Expression) -> 'State':
        """Assume that some condition holds in the current state.
        
        :param condition: expression representing the assumed condition
        :return: current state modified to satisfy the assumption
        """

    def assume(self, condition: Set[Expression]) -> 'State':
        """Assume that some condition holds in the current state.
        
        :param condition: set of expressions representing the assumed condition
        :return: current state modified to satisfy the assumption
        """
        self.big_join([deepcopy(self)._assume(expr) for expr in condition])
        return self

    @abstractmethod
    def enter_loop(self):
        """Enter a loop.
        
        :return: current state modified to enter a loop
        """

    @abstractmethod
    def _evaluate_expression(self, expression: Expression) -> Set[Expression]:
        """Retrieve a constant value. Account for side-effects by modifying the current state.
        
        :param expression: expression to retrieve the value of
        :return: set of expressions representing the constant value
        """

    def evaluate_expression(self, expression: Expression) -> 'State':
        """Evaluate a constant.
        
        :param expression: expression to be evaluated
        :return: current state modified by the constant evaluation
        """
        self.result = self._evaluate_expression(expression)
        return self

    @abstractmethod
    def exit_loop(self):
        """Exit a loop.

        :return: current state modified to exit a loop
        """

    def filter(self) -> 'State':
        """Assume that the current result holds in the current state.

        :return: current state modified to satisfy the current result
        """
        self.assume(self.result)
        self.result = set()         # filtering has no result, only side-effects
        return self

    @abstractmethod
    def _substitute_variable(self, left: Expression, right: Expression) -> 'State':
        """Substitute an expression to a variable.

        :param left: expression representing the variable to be substituted
        :param right: expression to substitute
        :return: current state modified by the variable substitution
        """

    def substitute_variable(self, left: Set[Expression], right: Set[Expression]) -> 'State':
        """Substitute an expression to a variable.
        
        :param left: set of expressions representing the variable to be substituted
        :param right: set of expressions representing the expression to substitute
        :return: current state modified by the variable substitution
        """
        self.big_join([deepcopy(self)._substitute_variable(lhs, rhs) for lhs in left for rhs in right])
        self.result = set()  # assignments have no result, only side-effects
        return self
