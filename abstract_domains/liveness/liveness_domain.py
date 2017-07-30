"""
Live Variable Abstract Domain
=============================

Abstract domain to be used for **live variable analysis**.
A program variable is *live* in a state if its value may be used before the variable is redefined.
"""

from enum import IntEnum
from typing import List, Set
from abstract_domains.store import Store
from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.utils import copy_docstring
from core.expressions import Expression, VariableIdentifier


class LivenessLattice(Lattice):
    """Liveness lattice::

        Live
          |
        Dead

    The default lattice element is ``Dead``.

    .. document private methods
    .. automethod:: LivenessLattice._less_equal
    .. automethod:: LivenessLattice._meet
    .. automethod:: LivenessLattice._join
    .. automethod:: LivenessLattice._widening
    """
    class Status(IntEnum):
        """Liveness status. The current lattice element is ether ``Live`` or ``Dead``."""
        Live = 1
        Dead = 0

    def __init__(self, liveness: Status = Status.Dead):
        super().__init__()
        self._element = liveness

    @property
    def element(self):
        """Current lattice element."""
        return self._element

    def __repr__(self):
        return self.element.name

    @copy_docstring(Lattice.bottom)
    def bottom(self):
        """The bottom lattice element is ``Dead``."""
        self.replace(LivenessLattice(LivenessLattice.Status.Dead))
        return self

    @copy_docstring(Lattice.top)
    def top(self):
        """The top lattice element is ``Live``."""
        self.replace(LivenessLattice(LivenessLattice.Status.Live))
        return self

    @copy_docstring(Lattice.is_bottom)
    def is_bottom(self):
        return self.element == LivenessLattice.Status.Dead

    @copy_docstring(Lattice.is_top)
    def is_top(self):
        return self.element == LivenessLattice.Status.Live

    @copy_docstring(Lattice.less_equal)
    def _less_equal(self, other: 'LivenessLattice') -> bool:
        return self.element < other.element

    @copy_docstring(Lattice._meet)
    def _meet(self, other: 'LivenessLattice'):
        self.replace(LivenessLattice(min(self.element, other.element)))
        return self

    @copy_docstring(Lattice._join)
    def _join(self, other: 'LivenessLattice') -> 'LivenessLattice':
        self.replace(LivenessLattice(max(self.element, other.element)))
        return self

    @copy_docstring(Lattice._widening)
    def _widening(self, other: 'LivenessLattice'):
        return self._join(other)


class LivenessState(Store, State):
    """Live variable analysis state. An element of the live variable abstract domain.

    Map from each program variable to its liveness status. All program variables are *dead* by default.

    .. document private methods
    .. automethod:: LivenessState._assign_variable
    .. automethod:: LivenessState._assume
    .. automethod:: LivenessState._output
    .. automethod:: LivenessState._substitute_variable
    """
    def __init__(self, variables: List[VariableIdentifier]):
        """Map each program variable to its liveness status.

        :param variables: list of program variables
        """
        super().__init__(variables, {int: LivenessLattice})

    @copy_docstring(State._access_variable)
    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    @copy_docstring(State._assign_variable)
    def _assign_variable(self, left: Expression, right: Expression) -> 'LivenessState':
        raise NotImplementedError("Variable assignment is not implemented!")

    @copy_docstring(State._assume)
    def _assume(self, condition: Expression) -> 'LivenessState':
        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                self.store[identifier] = LivenessLattice(LivenessLattice.Status.Live)
        return self

    @copy_docstring(State._evaluate_literal)
    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    @copy_docstring(State.enter_if)
    def enter_if(self):
        return self  # nothing to be done

    @copy_docstring(State.exit_if)
    def exit_if(self):
        return self  # nothing to be done

    @copy_docstring(State.enter_loop)
    def enter_loop(self):
        return self  # nothing to be done

    @copy_docstring(State.exit_loop)
    def exit_loop(self):
        return self  # nothing to be done

    @copy_docstring(State._output)
    def _output(self, output: Expression) -> 'LivenessState':
        return self  # nothing to be done

    @copy_docstring(State._substitute_variable)
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
