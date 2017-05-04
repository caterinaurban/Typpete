from typing import List, Set
from abstract_domains.state import State
from abstract_domains.usage.used import UsedLattice, Used
from abstract_domains.generic_lattices import StoreLattice
from core.expressions import Expression, VariableIdentifier


class UsedStore(StoreLattice, State):
    def __init__(self, variables: List[VariableIdentifier]):
        super().__init__(variables, UsedLattice)
        self._inside_print = False

    # def __repr__(self):
    #     result = super(State).__repr__()
    #     variables = super(StoreLattice).__repr__()
    #     return "[{}]\n{}".format(result, variables)

    @property
    def inside_print(self):
        return self._inside_print

    @inside_print.setter
    def inside_print(self, flag: bool):
        self._inside_print = flag

    def __repr__(self):
        variables = ", ".join("{} -> {}".format(variable, value) for variable, value in self.variables.items())
        return variables

    def descend(self) -> 'UsedStore':
        for var in self.variables.values():
            var.descend()
        return self

    def combine(self, other: 'UsedStore') -> 'UsedStore':
        for var, used in self.variables.items():
            used.combine(other.variables[var])
        return self

    def _use(self, x: VariableIdentifier, e: Expression):
        if self.variables[x].used in [Used.U, Used.S]:
            for identifier in e.ids():
                self.variables[identifier].used = Used.U
        return self

    def _kill(self, x: VariableIdentifier, e: Expression):
        if self.variables[x].used in [Used.U, Used.S]:
            if x in [v for v, u in self.variables.items() if v in e.ids()]:
                self.variables[x].used = Used.U  # x is still used since it is used in assigned expression
            else:
                self.variables[x].used = Used.O  # x is overwritten
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        if self._inside_print:
            self.variables[variable].used = Used.U
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'UsedStore':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume(self, condition: Expression) -> 'UsedStore':
        for identifier in condition.ids():
            if isinstance(identifier, VariableIdentifier):
                # update to U if exists a variable y in state that is either U or O (note that S is not enough)
                # or is set intersection, if checks if resulting list is empty
                if set([lat.used for lat in self.variables.values()]).intersection([Used.U, Used.O]):
                    self.variables[identifier].used = Used.U
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_loop(self):
        raise NotImplementedError("UsedStore does not support enter_loop")

    def exit_loop(self):
        raise NotImplementedError("UsedStore does not support exit_loop")

    def enter_if(self):
        raise NotImplementedError("UsedStore does not support enter_if")

    def exit_if(self):
        raise NotImplementedError("UsedStore does not support exit_if")

    def _substitute_variable(self, left: Expression, right: Expression) -> 'UsedStore':
        if isinstance(left, VariableIdentifier):
            self._use(left, right)._kill(left, right)
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))
        return self
