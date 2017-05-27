from copy import deepcopy
from typing import List, Set

from abstract_domains.generic_lattices import StackLattice
from abstract_domains.state import State
from abstract_domains.usage.store import UsedStore
from core.expressions import Expression, VariableIdentifier


class UsedStack(StackLattice, State):
    def __init__(self, variables: List[VariableIdentifier]):
        """Usage-analysis state representation.

        :param variables: list of program variables
        """
        super().__init__(UsedStore, {'variables': variables})
        self._inside_print = False

    @property
    def inside_print(self):
        return self._inside_print

    @inside_print.setter
    def inside_print(self, flag: bool):
        self._inside_print = flag
        for store in self.stack:
            store.inside_print = flag

    # def __repr__(self):
    #     result = super(State).__repr__()
    #     stack = super(StackLattice).__repr__()
    #     return "[{}]\n{}".format(result, stack)

    def push(self):
        if self.is_bottom():
            return self
        self.stack.append(deepcopy(self.stack[-1]).descend())
        return self

    def pop(self):
        if self.is_bottom():
            return self
        popped = self.stack.pop()
        self.stack[-1].combine(popped)
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        self.stack[-1].access_variable(variable)
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'UsedStack':
        self.stack[-1].assume({condition})
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        self.stack[-1].evaluate_literal(literal)
        return {literal}

    def enter_loop(self):
        return self.enter_if()

    def exit_loop(self):
        return self.exit_if()

    def enter_if(self):
        if self.is_bottom():
            return self
        self.push()
        return self

    def exit_if(self):
        if self.is_bottom():
            return self
        self.pop()
        return self

    def _output(self, output: Expression) -> 'UsedStack':
        return self  # nothing to be done

    def _substitute_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        if isinstance(left, VariableIdentifier):
            self.stack[-1].substitute_variable({left}, {right})  # TODO correct to use non-underscore interface???
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
