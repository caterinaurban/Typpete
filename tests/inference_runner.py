from frontend.pre_analysis import PreAnalyzer
import frontend.z3_types as z3_types
import ast

r = open("tests/inference/functions_test.py")
t = ast.parse(r.read())

analyzer = PreAnalyzer(t)

z3_types.init_types({
    "max_tuple_length": analyzer.maximum_tuple_length(),
    "max_function_args": analyzer.maximum_function_args()
})

from frontend.stmt_inferrer import *

context = Context()
for stmt in t.body:
    infer(stmt, context)

z3_types.solver.push()
z3_types.solver.check()
model = z3_types.solver.model()

for v in context.types_map:
    z3_t = context.types_map[v]
    print("{}: {}".format(v, model[z3_t]))
