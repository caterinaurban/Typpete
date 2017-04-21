import core.expressions
from abstract_domains.used_analysis.states import UsedStack
from core.cfg import Basic, Unconditional, ControlFlowGraph, Conditional
from core.statements import ProgramPoint, ExpressionEvaluation, VariableAccess, Assignment
from engine.backward import BackwardInterpreter
from visualization.graph_renderer import CfgRenderer

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

stmt1 = Assignment(p11, VariableAccess(p11, x), ExpressionEvaluation(p13, two))         # x := 2
print("stmt1: {}".format(stmt1))
stmt2 = Assignment(p21, VariableAccess(p21, y), ExpressionEvaluation(p23, four))        # y := 4
print("stmt2: {}".format(stmt2))
stmt3 = Assignment(p31, VariableAccess(p31, x), ExpressionEvaluation(p33, one))         # x := 1
print("stmt3: {}".format(stmt3))
expr4 = core.expressions.BinaryComparisonOperation(int, y, core.expressions.BinaryComparisonOperation.Operator.Gt, x)
stmt4 = ExpressionEvaluation(p42, expr4)                                                # y > x
print("stmt4: {}".format(expr4))
stmt5 = Assignment(p52, VariableAccess(p52, z), VariableAccess(p54, y))                 # z := y
print("stmt5: {}".format(stmt5))
neg_expr4 = core.expressions.UnaryBooleanOperation(bool, core.expressions.UnaryBooleanOperation.Operator.Neg, expr4)
neg_stmt4 = ExpressionEvaluation(p42, neg_expr4)                                        # !(y > x)
print("!stmt4: {}".format(neg_stmt4))
expr6 = core.expressions.BinaryArithmeticOperation(int, y, core.expressions.BinaryArithmeticOperation.Operator.Mul, y)
stmt6 = Assignment(p62, VariableAccess(p62, z), ExpressionEvaluation(p64, expr6))       # z := y * y
print("stmt6: {}".format(stmt6))
stmt7 = ExpressionEvaluation(p71, core.expressions.Print(int, z))                 # print(z)
print("stmt5: {}".format(stmt5))

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
e23 = Conditional(n2, stmt4, n3)
print("e23: {}".format(e23))
e35 = Unconditional(n3, n5)
print("e35: {}".format(e35))
e24 = Conditional(n2, neg_stmt4, n4)
print("e24: {}".format(e24))
e45 = Unconditional(n4, n5)
print("e45: {}".format(e45))
e56 = Unconditional(n5, n6)
print("e56: {}".format(e56))

cfg = ControlFlowGraph({n1, n2, n3, n4, n5, n6}, n1, n6, {e12, e23, e35, e24, e45, e56})

# render cfg graph
CfgRenderer().render(cfg, label=__file__)

# Used Analysis
print("\nUsed Analysis\n")

backward_interpreter = BackwardInterpreter(cfg, 3)
used_analysis = backward_interpreter.analyze(UsedStack([x, y, z]))
print("{}".format(used_analysis))
