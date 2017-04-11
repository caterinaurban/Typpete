from core.cfg import Basic, Unconditional, ControlFlowGraph
from copy import deepcopy

from engine.forward import ForwardInterpreter
from abstract_domains.lattice import Lattice
from engine.result import AnalysisResult
from core.statements import ProgramPoint, ConstantEvaluation, VariableAccess, Assignment
from core.expressions import Expression, Constant, VariableIdentifier
from abstract_domains.state import State
from typing import Dict, List, Set

# Statements
print("\nStatements\n")

x = VariableIdentifier(int, 'x')
y = VariableIdentifier(int, 'y')
o = Constant(int, '1')
t = Constant(int, '3')

p11 = ProgramPoint(1, 1)
p13 = ProgramPoint(1, 3)
p21 = ProgramPoint(2, 1)
p23 = ProgramPoint(2, 3)
p31 = ProgramPoint(3, 1)
p33 = ProgramPoint(3, 3)

stmt1 = Assignment(p11, VariableAccess(p11, x), ConstantEvaluation(p13, o))    # x = 1
print("s1: {}".format(stmt1))
stmt2 = Assignment(p21, VariableAccess(p21, y), ConstantEvaluation(p23, t))    # y = 3
print("s2: {}".format(stmt2))
stmt3 = Assignment(p31, VariableAccess(p31, x), VariableAccess(p33, y))        # x = y
print("s3: {}".format(stmt3))

# Control Flow Graph
print("\nControl Flow Graph\n")

n1 = Basic(1, list())
print("n1: {}".format(n1))
n2 = Basic(2, [stmt1, stmt2, stmt3])
print("n2: {}".format(n2))
n3 = Basic(3, list())
print("n3: {}".format(n3))

e12 = Unconditional(n1, n2)
print("e12: {}".format(e12))
e23 = Unconditional(n2, n3)
print("e23: {}".format(e23))

cfg = ControlFlowGraph({n1, n2, n3}, n1, n3, {e12, e23})

# Analysis
print("\nAnalysis\n")


class DummyState(State):

    class Internal(State.Internal):
        def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind, result: Set[Expression]):
            super().__init__(kind, result)
            self._variables = {variable: Constant(int, '0') for variable in variables}

        @property
        def variables(self):
            return self._variables

        @variables.setter
        def variables(self, variables):
            self._variables = variables

    def __init__(self, variables: List[VariableIdentifier],
                 kind: Lattice.Kind = Lattice.Kind.Default, result: Set[Expression] = set()):
        super().__init__(kind, result)
        self._internal = DummyState.Internal(variables, kind, result)

    @property
    def internal(self):
        return self._internal

    @property
    def variables(self):
        return self.internal.variables

    @variables.setter
    def variables(self, variables: Dict[VariableIdentifier, Constant]):
        self.internal.variables = variables

    def __str__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        variables = "".join("\n{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return "[{}] {}".format(result, variables)

    def less_equal_default(self, other: 'DummyState') -> bool:
        result = True
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            result = result and int(l.val) < int(r.val)
        return result

    def join_default(self, other: 'DummyState') -> 'DummyState':
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            if int(r.val) > int(l.val):
                self.variables[var] = r
        return self

    def meet_default(self, other: 'DummyState') -> 'DummyState':
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            if int(r) < int(l):
                self.variables[var] = r
        return self

    def widening_default(self, other: 'DummyState') -> 'DummyState':
        return self.join_default(other)

    def access_variable_value(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def assign_variable_expression(self, left: Expression, right: Expression) -> 'DummyState':
        if isinstance(left, VariableIdentifier):
            if isinstance(right, Constant):
                self.variables[left] = right
            elif isinstance(right, VariableIdentifier):
                self.variables[left] = self.variables[right]
            else:
                NotImplementedError("")
            return self
        else:
            NotImplementedError("")

    def evaluate_constant_value(self, constant: Constant):
        return {constant}

    def substitute_variable_expression(self, left: Expression, right: Expression):
        NotImplementedError("")


s1 = DummyState([x, y])
# print("s1: {}\n".format(s1))
s2 = deepcopy(s1)
stmt1.forward_semantics(s2)
# print("s2: {}\n".format(s2))
s3 = deepcopy(s2)
stmt2.forward_semantics(s3)
# print("s3: {}\n".format(s3))
s4 = deepcopy(s3)
stmt3.forward_semantics(s4)
# print("s4: {}".format(s4))

analysis = AnalysisResult(cfg)
analysis.set_node_result(n1, [s1])
analysis.set_node_result(n2, [s1, s2, s3, s4])
analysis.set_node_result(n3, [s4])
# print("{}".format(analysis))

interpreter = ForwardInterpreter(cfg, 3)
analysis = interpreter.analyze(DummyState([x, y]))
print("{}".format(analysis))
