from enum import IntEnum
from typing import List, Set

from abstract_domains.generic_lattices import StoreLattice
from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier


class LiveDeadLattice(Lattice):
    class Liveness(IntEnum):
        """Liveness state of a program variable."""
        Dead = 0  # dead variable
        Live = 1  # live variable

    def __init__(self, initial_element: 'LiveDeadLattice.Liveness' = None):
        super().__init__(initial_element)

    def default(self):
        self.element = LiveDeadLattice.Liveness.Dead
        return self

    def _less_equal(self, other: 'LiveDeadLattice') -> bool:
        return self.element < other.element

    def _meet(self, other: 'LiveDeadLattice'):
        self.element = min(self.element, other.element)
        return self

    def _join(self, other: 'LiveDeadLattice') -> 'LiveDeadLattice':
        self.element = max(self.element, other.element)
        return self

    def _widening(self, other: 'LiveDeadLattice'):
        return self._join(other)


class LiveDead(StoreLattice, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Live/Dead variable analysis state representation.
        
        :param variables: list of program variables
        """
        super().__init__(variables, LiveDeadLattice)

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'LiveDead':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'LiveDead':
        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                self.variables[identifier] = LiveDeadLattice(LiveDeadLattice.Liveness.Live)
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_loop(self):
        return self  # nothing to be done

    def exit_loop(self):
        return self  # nothing to be done

    def enter_if(self):
        return self  # nothing to be done

    def exit_if(self):
        return self  # nothing to be done

    def _output(self, output: Expression) -> 'LiveDead':
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression) -> 'LiveDead':
        if isinstance(left, VariableIdentifier):
            self.variables[left] = LiveDeadLattice(LiveDeadLattice.Liveness.Dead)
            for identifier in right.ids():
                if isinstance(identifier, VariableIdentifier):
                    self.variables[identifier] = LiveDeadLattice(LiveDeadLattice.Liveness.Live)
                else:
                    raise NotImplementedError("")
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
