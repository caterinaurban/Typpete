from enum import IntEnum
from typing import List, Set
from abstract_domains.store import Store
from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier


class LivenessLattice(Lattice):
    class Status(IntEnum):
        """Liveness status of a program variable."""
        Live = 1  # live variable
        Dead = 0  # dead variable

    def __init__(self, liveness: Status = Status.Dead):
        super().__init__()
        self._element = liveness

    @property
    def element(self):
        return self._element

    def __repr__(self):
        return self.element.name

    def bottom(self):
        self.replace(LivenessLattice(LivenessLattice.Status.Dead))
        return self

    def top(self):
        self.replace(LivenessLattice(LivenessLattice.Status.Live))
        return self

    def is_bottom(self):
        return self.element == LivenessLattice.Status.Dead

    def is_top(self):
        return self.element == LivenessLattice.Status.Live

    def _less_equal(self, other: 'LivenessLattice') -> bool:
        return self.element < other.element

    def _meet(self, other: 'LivenessLattice'):
        self.replace(LivenessLattice(min(self.element, other.element)))
        return self

    def _join(self, other: 'LivenessLattice') -> 'LivenessLattice':
        self.replace(LivenessLattice(max(self.element, other.element)))
        return self

    def _widening(self, other: 'LivenessLattice'):
        return self._join(other)


class LivenessState(Store, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Liveness variable analysis state representation.
        
        :param variables: list of program variables
        """
        super().__init__(variables, {int: LivenessLattice})

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'LivenessState':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'LivenessState':
        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                self.store[identifier] = LivenessLattice(LivenessLattice.Status.Live)
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_if(self):
        return self  # nothing to be done

    def exit_if(self):
        return self  # nothing to be done

    def enter_loop(self):
        return self  # nothing to be done

    def exit_loop(self):
        return self  # nothing to be done

    def _output(self, output: Expression) -> 'LivenessState':
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression) -> 'LivenessState':
        if isinstance(left, VariableIdentifier):
            self.store[left] = LivenessLattice(LivenessLattice.Status.Dead)
            for identifier in right.ids():
                if isinstance(identifier, VariableIdentifier):
                    self.store[identifier] = LivenessLattice(LivenessLattice.Status.Live)
                else:
                    raise NotImplementedError(f"Variable substitution with {right} is not implemented!")
        else:
            raise NotImplementedError(f"Variable substitution for {left} is not implemented!")
        return self
