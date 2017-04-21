from copy import deepcopy
from typing import List, Set

from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from abstract_domains.usage.lattices import UsedLattice, Used
from core.expressions import Expression, VariableIdentifier, Print


class UsedStack(State):
    class Internal(State.Internal):
        def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind):
            super().__init__(kind)
            self._stack = [UsedStore(variables)]

        @property
        def stack(self):
            return self._stack

    def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind = Lattice.Kind.Default):
        """Used variable analysis state representation.

        :param variables: list of program variables
        :param kind: kind of lattice element
        """
        super().__init__(kind)
        self._internal = UsedStack.Internal(variables, kind)

    @property
    def stack(self):
        return self.internal.stack

    def __str__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        return "[{}] {}".format(result, " | ".join(self.stack))

    def push(self):
        self.stack.append(deepcopy(self.stack[-1]).descend())
        return self

    def pop(self):
        popped = self.stack.pop()
        self.stack[-1].combine(popped)
        return self

    def _less_equal(self, other: 'UsedStack') -> bool:
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        result = True
        for i, _ in enumerate(self.stack):
            l = self.stack[i]
            r = other.stack[i]
            result = result and l.less_equal(r)
        return result

    def _meet(self, other: 'UsedStack'):
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, store in enumerate(self.stack):
            store.meet(other.stack[i])
        return self

    def _join(self, other: 'UsedStack') -> 'UsedStack':
        if len(self.stack) != len(other.stack):
            raise Exception("Stacks must be equally long")
        for i, store in enumerate(self.stack):
            store.join(other.stack[i])
        return self

    def _widening(self, other: 'UsedStack'):
        return self._join(other)

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'UsedStack':
        self.stack[-1].assume({condition})
        # TODO pop frame (where to push?)
        return self

    def _evaluate_expression(self, expression: Expression) -> Set[Expression]:
        self.stack[-1].evaluate_expression({expression})
        return {expression}

    def _substitute_variable(self, left: Expression, right: Expression) -> 'UsedStack':
        if isinstance(left, VariableIdentifier):
            self.stack[-1].substitute_variable({left}, {right})  # correct to use non-underscore interface???
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
