from abstract_domains.liveness.livedead import LiveDead
from core.cfg import Basic, Unconditional, ControlFlowGraph, Conditional, Edge
import core.expressions
from core.statements import ProgramPoint, LiteralEvaluation, VariableAccess, Assignment, Call
from engine.backward import BackwardInterpreter
from semantics.backward import DefaultBackwardSemantics
from visualization.graph_renderer import AnalysisResultRenderer

# Expressions and Statements
print("\nExpressions and Statements\n")

x = core.expressions.VariableIdentifier(int, "x")
y = core.expressions.VariableIdentifier(int, "y")
z = core.expressions.VariableIdentifier(int, "z")
one = core.expressions.Literal(int, "1")
two = core.expressions.Literal(int, "2")
four = core.expressions.Literal(int, "4")

# 1: x := 2
# 2: y := 4
# 3: x := 1
# 4: if y > x:
# 5:    z := y
#    else:
# 6:    z := y * y
# 7: x := z

p11 = ProgramPoint(1, 1)
p13 = ProgramPoint(1, 3)
p21 = ProgramPoint(2, 1)
p23 = ProgramPoint(2, 3)
p31 = ProgramPoint(3, 1)
p33 = ProgramPoint(3, 3)
p42 = ProgramPoint(4, 2)
p52 = ProgramPoint(5, 2)
p54 = ProgramPoint(5, 4)
p62 = ProgramPoint(6, 2)
p64 = ProgramPoint(6, 4)
p71 = ProgramPoint(7, 1)
p73 = ProgramPoint(7, 3)

stmt1 = Assignment(p11, VariableAccess(p11, x), LiteralEvaluation(p13, two))
print("stmt1: {}".format(stmt1))                                                    # x := 2
stmt2 = Assignment(p21, VariableAccess(p21, y), LiteralEvaluation(p23, four))
print("stmt2: {}".format(stmt2))                                                    # y := 4
stmt3 = Assignment(p31, VariableAccess(p31, x), LiteralEvaluation(p33, one))
print("stmt3: {}".format(stmt3))                                                    # x := 1
stmt4 = Call(p42, "gt", [VariableAccess(p42, y), VariableAccess(p42, x)], bool)
print("stmt4: {}".format(stmt4))                                                    # y > x
stmt5 = Assignment(p52, VariableAccess(p52, z), VariableAccess(p54, y))
print("stmt5: {}".format(stmt5))                                                    # z := y
neg_stmt4 = Call(p42, "not", [stmt4], bool)
print("!stmt4: {}".format(neg_stmt4))                                               # !(y > x)
stmt6 = Assignment(p62, VariableAccess(p62, z), Call(p64, "mul", [VariableAccess(p64, y), VariableAccess(p64, y)], int))
print("stmt6: {}".format(stmt6))                                                    # z := y * y
stmt7 = Assignment(p71, VariableAccess(p71, x), VariableAccess(p73, z))
print("stmt5: {}".format(stmt5))                                                    # x := z

# Control Flow Graph
print("\nControl Flow Graph\n")

n1 = Basic(1, list())
print("entry: {}".format(n1))
n2 = Basic(2, [stmt1, stmt2, stmt3])
print("n2: {}".format(n2))
n3 = Basic(3, [stmt5])
print("n3: {}".format(n3))
n4 = Basic(4, [stmt6])
print("n4: {}".format(n4))
n5 = Basic(5, [stmt7])
print("n5: {}".format(n5))
n6 = Basic(6, list())
print("exit: {}".format(n6))

e12 = Unconditional(n1, n2)
print("e12: {}".format(e12))
e23 = Conditional(n2, stmt4, n3, Edge.Kind.IF_IN)
print("e23: {}".format(e23))
e35 = Unconditional(n3, n5, Edge.Kind.IF_OUT)
print("e35: {}".format(e35))
e24 = Conditional(n2, neg_stmt4, n4, Edge.Kind.IF_IN)
print("e24: {}".format(e24))
e45 = Unconditional(n4, n5, Edge.Kind.IF_OUT)
print("e45: {}".format(e45))
e56 = Unconditional(n5, n6)
print("e56: {}".format(e56))

cfg = ControlFlowGraph({n1, n2, n3, n4, n5, n6}, n1, n6, {e12, e23, e35, e24, e45, e56})

# Live/Dead Analysis
print("\nLive/Dead Analysis\n")

backward_interpreter = BackwardInterpreter(cfg, DefaultBackwardSemantics(), 3)
liveness_analysis = backward_interpreter.analyze(LiveDead([x, y, z]))
AnalysisResultRenderer().render((cfg, liveness_analysis), label=__file__)
