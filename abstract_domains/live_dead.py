from enum import Enum
from abstract_domains.lattice import Lattice
from core.expressions import Expression, Constant, VariableIdentifier
from abstract_domains.state import State
from typing import List, Set


class LiveDead(State):
    class Liveness(Enum):
        """Liveness state of a program variable."""
        Dead = -1   # dead variable
        Live = 1    # live variable

    class Internal(State.Internal):
        def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind, result: Set[Expression]):
            super().__init__(kind, result)
            self._variables = {variable: LiveDead.Liveness.Dead for variable in variables}

        @property
        def variables(self):
            return self._variables

    def __init__(self, variables: List[VariableIdentifier],
                 kind: Lattice.Kind = Lattice.Kind.Default, result: Set[Expression] = set()):
        """Live/Dead variable analysis state representation.
        
        :param variables: list of program variables
        :param kind: kind of lattice element
        :param result: set of expressions representing the result of the previously analyzed statement
        """
        super().__init__(kind, result)
        self._internal = LiveDead.Internal(variables, kind, result)

    @property
    def internal(self):
        return self._internal

    @property
    def variables(self):
        return self.internal.variables

    def __str__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        variables = "".join("\n{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return "[{}] {}".format(result, variables)

    def less_equal_default(self, other: 'LiveDead') -> bool:
        result = True
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            result = result and not (l is LiveDead.Liveness.Live and r is LiveDead.Liveness.Dead)
        return result

    def meet_default(self, other: 'LiveDead'):
        for var in self.variables:
            if self.variables[var] is LiveDead.Liveness.Dead or other.variables[var] is LiveDead.Liveness.Dead:
                self.variables[var] = LiveDead.Liveness.Dead
        return self

    def join_default(self, other: 'LiveDead') -> 'LiveDead':
        for var in self.variables:
            if self.variables[var] is LiveDead.Liveness.Live or other.variables[var] is LiveDead.Liveness.Live:
                self.variables[var] = LiveDead.Liveness.Live
        return self

    def widening_default(self, other: 'LiveDead'):
        return self.join_default(other)

    def access_variable_value(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def assign_variable_expression(self, left: Expression, right: Expression) -> 'LiveDead':
        return self

    def evaluate_constant_value(self, constant: Constant) -> Set[Expression]:
        return {constant}

    def substitute_variable_expression(self, left: Expression, right: Expression) -> 'LiveDead':
        if isinstance(left, VariableIdentifier):
            self.variables[left] = LiveDead.Liveness.Dead
            if isinstance(right, Constant):
                pass
            elif isinstance(right, VariableIdentifier):
                self.variables[right] = LiveDead.Liveness.Live
            else:
                raise NotImplementedError("Variable substitution with {} not yet implemented!".format(right))
        else:
            raise NotImplementedError("Variable substitution for {} not yet implemented!".format(left))
        return self
