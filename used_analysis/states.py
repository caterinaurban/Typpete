from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier, Print
from enum import Enum
from typing import List, Set
from used_analysis.lattices import UsedLattice, Used
from copy import deepcopy


class UsedStore(State):
    class Internal(State.Internal):
        def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind):
            super().__init__(kind)
            self._variables = {variable: UsedLattice(Used.N) for variable in variables}

        @property
        def variables(self):
            return self._variables

    def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind = Lattice.Kind.Default):
        """Used variable analysis state representation.
        
        :param variables: list of program variables
        :param kind: kind of lattice element
        """
        super().__init__(kind)
        self._internal = UsedStore.Internal(variables, kind)

    @property
    def variables(self):
        return self.internal.variables

    def __str__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        variables = "".join("\n{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return "[{}] {}".format(result, variables)

    def _less_equal(self, other: 'UsedStore') -> bool:
        result = True
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            result = result and l.less_equal(r)
        return result

    def _meet(self, other: 'UsedStore'):
        for var in self.variables:
            self.variables[var].meet(other.variables[var])
        return self

    def _join(self, other: 'UsedStore') -> 'UsedStore':
        for var in self.variables:
            self.variables[var].join(other.variables[var])
        return self

    def _widening(self, other: 'UsedStore'):
        return self._join(other)

    def _use(self, x: VariableIdentifier, e: Expression):
        if self.variables[x].used in [Used.U, Used.UU]:
            for identifier in e.ids():
                self.variables[identifier].used = Used.U
        return self

    def descend(self) -> 'UsedStore':
        for var in self.variables:
            var.descend()
        return self

    def combine(self, other: 'UsedStore') -> 'UsedStore':
        for i,var in enumerate(self.variables):
            var.combine(other.variables[i])
        return self

    def _kill(self, x: VariableIdentifier, e: Expression):
        if set([lat.used for id, lat in self.variables.items() if id in e.ids()]).intersection([Used.U, Used.UU]):
            self.variables[x].used = Used.U  # x is still used since it is used in assigned expression
        elif self.variables[x].used in [Used.U, Used.UU]:
            self.variables[x].used = Used.UN  # x is overwritten
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'UsedStore':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'UsedStore':
        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                # update to U if exists a variable y in state that is either U or UN (note that UU is not enough)
                # or is set intersection, if checks if resulting list is empty
                if set([lat.used for lat in self.variables.values()]).intersection([Used.U, Used.UN]):
                    self.variables[identifier].used = Used.U
        return self

    def _evaluate_expression(self, expression: Expression) -> Set[Expression]:
        if isinstance(expression, Print):
            for identifier in expression.ids():
                self.variables[identifier].used = Used.U
        return {expression}

    def _substitute_variable(self, left: Expression, right: Expression) -> 'UsedStore':
        if isinstance(left, VariableIdentifier):
            self._use(left, right)._kill(left, right)
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self


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
