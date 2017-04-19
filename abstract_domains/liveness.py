from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier
from enum import Enum
from typing import List, Set


class LiveDead(State):
    class Liveness(Enum):
        """Liveness state of a program variable."""
        Dead = -1  # dead variable
        Live = 1  # live variable

    def __init__(self, variables: List[VariableIdentifier]):
        """Live/Dead variable analysis state representation.
        
        :param variables: list of program variables
        """
        super().__init__()
        self._variables = {variable: LiveDead.Liveness.Dead for variable in variables}

    @property
    def variables(self):
        return self._variables

    def __repr__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        variables = "".join("\n{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return "[{}] {}".format(result, variables)

    def default(self):
        return self.bottom()

    def bottom(self):
        self._variables = {variable: LiveDead.Liveness.Dead for variable in self.variables}
        return self

    def top(self):
        self._variables = {variable: LiveDead.Liveness.Live for variable in self.variables}
        return self

    def is_bottom(self) -> bool:
        return all(val == LiveDead.Liveness.Dead for val in self.variables.values())

    def is_top(self) -> bool:
        return all(val == LiveDead.Liveness.Dead for val in self.variables.values())

    def _less_equal(self, other: 'LiveDead') -> bool:
        result = True
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            result = result and not (l is LiveDead.Liveness.Live and r is LiveDead.Liveness.Dead)
        return result

    def _meet(self, other: 'LiveDead'):
        for var in self.variables:
            if self.variables[var] is LiveDead.Liveness.Dead or other.variables[var] is LiveDead.Liveness.Dead:
                self.variables[var] = LiveDead.Liveness.Dead
        return self

    def _join(self, other: 'LiveDead') -> 'LiveDead':
        for var in self.variables:
            if self.variables[var] is LiveDead.Liveness.Live or other.variables[var] is LiveDead.Liveness.Live:
                self.variables[var] = LiveDead.Liveness.Live
        return self

    def _widening(self, other: 'LiveDead'):
        return self._join(other)

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'LiveDead':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'LiveDead':

        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                self.variables[identifier] = LiveDead.Liveness.Live
        return self

    def enter_loop(self):
        return self  # nothing to be done

    def _evaluate_expression(self, expression: Expression) -> Set[Expression]:
        return {expression}

    def exit_loop(self):
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression) -> 'LiveDead':
        if isinstance(left, VariableIdentifier):
            self.variables[left] = LiveDead.Liveness.Dead
            for identifier in right.ids():
                if isinstance(identifier, VariableIdentifier):
                    self.variables[identifier] = LiveDead.Liveness.Live
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
