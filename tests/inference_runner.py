from frontend.stmt_inferrer import *
from frontend.context import Context
import frontend.z3_types as z3_types

r = open("tests/expressions_test.py")
t = ast.parse(r.read())
context = Context()
for stmt in t.body:
    infer(stmt, context)

z3_types.solver.push()
z3_types.solver.check()
model = z3_types.solver.model()

for v in context.types_map:
    z3_t = context.types_map[v]
    print("{}: {}".format(v, model[z3_t]))

