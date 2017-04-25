from typing import List, Set

from abstract_domains.generic_lattices import TopBottomLattice, StoreLattice
from abstract_domains.state import State
from core.cfg import Basic, Unconditional, ControlFlowGraph
from core.expressions import Expression, Literal, VariableIdentifier
from core.statements import ProgramPoint, LiteralEvaluation, VariableAccess, Assignment
from engine.forward import ForwardInterpreter
from semantics.forward import DefaultForwardSemantics
from visualization.graph_renderer import AnalysisResultRenderer

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
p41 = ProgramPoint(4, 1)
p43 = ProgramPoint(4, 3)
p45 = ProgramPoint(4, 5)

stmt1 = Assignment(p11, VariableAccess(p11, x), LiteralEvaluation(p13, o))  # x = 1
print("s1: {}".format(stmt1))
stmt2 = Assignment(p21, VariableAccess(p21, y), LiteralEvaluation(p23, t))  # y = 3
print("s2: {}".format(stmt2))
stmt3 = Assignment(p31, VariableAccess(p31, x), VariableAccess(p33, y))  # x = y
print("s3: {}".format(stmt3))
# stmt4 = Call(p41, "foo", [VariableAccess(p43, x), VariableAccess(p45, y)])  # foo(x, y)
# print("s4: {}".format(stmt4))

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


class DummyLattice(TopBottomLattice):
    def __init__(self):
        super().__init__(Literal(int, '0'))  # the default element can be set in superclass constructor

    def default(self):
        self.element = Literal(int, '0')  # the default element can be set via default method overwrite
        return self

    def _less_equal(self, other: 'DummyLattice') -> bool:
        return int(self.element.val) < int(other.element.val)  # compare the values of the literals

    def _meet(self, other: 'DummyLattice'):
        if int(other.element.val) < int(self.element.val):
            self.replace(other)
        return self

    def _join(self, other: 'DummyLattice') -> 'DummyLattice':
        if int(other.element.val) > int(self.element.val):
            self.replace(other)
        return self

    def _widening(self, other: 'DummyLattice'):
        return self._join(other)


class DummyState(StoreLattice, State):
    def __init__(self, variables: List[VariableIdentifier]):
        super().__init__(variables, DummyLattice)

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

forward_interpreter = ForwardInterpreter(cfg, DefaultForwardSemantics(), 3)
dummy_analysis = forward_interpreter.analyze(DummyState([x, y]))
AnalysisResultRenderer().render((cfg, dummy_analysis), label=__file__)
