from frontend.pre_analysis import PreAnalyzer
import frontend.z3_types as z3_types
import ast

r = open("tests/inference/classes_test.py")
t = ast.parse(r.read())

analyzer = PreAnalyzer(t)


config = analyzer.get_all_configurations()
z3_types.init_types(config)

from frontend.stmt_inferrer import *

context = Context()
for stmt in t.body:
    infer(stmt, context)

z3_types.solver.push()
check = z3_types.solver.check(z3_types.assertions)

try:
    model = z3_types.solver.model()
    for v in context.types_map:
        z3_t = context.types_map[v]
        print("{}: {}".format(v, model[z3_t]))
except z3_types.z3types.Z3Exception as e:
    print("Check: {}".format(check))
    if check == z3_types.unsat:
        print([z3_types.assertions_errors[x] for x in z3_types.solver.unsat_core()])

