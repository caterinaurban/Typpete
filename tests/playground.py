from abstract_domains.lattice import Lattice
from abstract_domains.state import State
from abstract_domains.liveness import LiveDead
from core.cfg import Basic, Unconditional, ControlFlowGraph
from core.expressions import Expression, Literal, VariableIdentifier
from core.statements import ProgramPoint, ExpressionEvaluation, VariableAccess, Assignment
from engine.backward import BackwardInterpreter
from engine.forward import ForwardInterpreter
from typing import Dict, List, Set

from visualization.graph_renderer import CfgRenderer

# Statements
print("\nStatements\n")

x = VariableIdentifier(int, 'x')
y = VariableIdentifier(int, 'y')
o = Literal(int, '1')
t = Literal(int, '3')

p11 = ProgramPoint(1, 1)
p13 = ProgramPoint(1, 3)
p21 = ProgramPoint(2, 1)
p23 = ProgramPoint(2, 3)
p31 = ProgramPoint(3, 1)
p33 = ProgramPoint(3, 3)

stmt1 = Assignment(p11, VariableAccess(p11, x), ExpressionEvaluation(p13, o))    # x = 1
print("s1: {}".format(stmt1))
stmt2 = Assignment(p21, VariableAccess(p21, y), ExpressionEvaluation(p23, t))    # y = 3
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

# render cfg graph
CfgRenderer().render(cfg, label=__file__)

# Analysis
print("\nAnalysis\n")


class DummyState(State):

    class Internal(State.Internal):
        def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind):
            super().__init__(kind)
            self._variables = {variable: Literal(int, '0') for variable in variables}

        @property
        def variables(self):
            return self._variables

        @variables.setter
        def variables(self, variables):
            self._variables = variables

    def __init__(self, variables: List[VariableIdentifier], kind: Lattice.Kind = Lattice.Kind.Default):
        super().__init__(kind)
        self._internal = DummyState.Internal(variables, kind)

    @property
    def internal(self):
        return self._internal

    @property
    def variables(self):
        return self.internal.variables

    @variables.setter
    def variables(self, variables: Dict[VariableIdentifier, Literal]):
        self.internal.variables = variables

    def __str__(self):
        result = ", ".join("{}".format(expression) for expression in self.result)
        variables = "".join("\n{} -> {} ".format(variable, value) for variable, value in self.variables.items())
        return "[{}] {}".format(result, variables)

    def _less_equal(self, other: 'DummyState') -> bool:
        result = True
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            result = result and int(l.val) < int(r.val)
        return result

    def _join(self, other: 'DummyState') -> 'DummyState':
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            if int(r.val) > int(l.val):
                self.variables[var] = r
        return self

    def _meet(self, other: 'DummyState') -> 'DummyState':
        for var in self.variables:
            l = self.variables[var]
            r = other.variables[var]
            if int(r) < int(l):
                self.variables[var] = r
        return self

    def _widening(self, other: 'DummyState') -> 'DummyState':
        return self._join(other)

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'DummyState':
        if isinstance(left, VariableIdentifier):
            if isinstance(right, Literal):
                self.variables[left] = right
            elif isinstance(right, VariableIdentifier):
                self.variables[left] = self.variables[right]
            else:
                raise NotImplementedError("")
        else:
            raise NotImplementedError("")
        return self

    def _assume(self, condition: Expression) -> 'DummyState':
        pass

    def _evaluate_expression(self, expression: Expression):
        return {expression}

    def _substitute_variable(self, left: Expression, right: Expression):
        raise NotImplementedError("")


# s1 = DummyState([x, y])
# print("s1: {}\n".format(s1))
# s2 = deepcopy(s1)
# stmt1.forward_semantics(s2)
# print("s2: {}\n".format(s2))
# s3 = deepcopy(s2)
# stmt2.forward_semantics(s3)
# print("s3: {}\n".format(s3))
# s4 = deepcopy(s3)
# stmt3.forward_semantics(s4)
# print("s4: {}".format(s4))

# dummy_analysis = AnalysisResult(cfg)
# dummy_analysis.set_node_result(n1, [s1])
# dummy_analysis.set_node_result(n2, [s1, s2, s3, s4])
# dummy_analysis.set_node_result(n3, [s4])
# print("{}".format(analysis))

forward_interpreter = ForwardInterpreter(cfg, 3)
dummy_analysis = forward_interpreter.analyze(DummyState([x, y]))
print("{}".format(dummy_analysis))

# Live/Dead Analysis
print("\nLive/Dead Analysis\n")

backward_interpreter = BackwardInterpreter(cfg, 3)
liveness_analysis = backward_interpreter.analyze(LiveDead([x, y]))
print("{}".format(liveness_analysis))
