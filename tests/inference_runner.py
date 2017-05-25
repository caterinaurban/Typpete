from frontend.pre_analysis import PreAnalyzer
from frontend.stmt_inferrer import *
from frontend.stubs.stubs_handler import StubsHandler
import frontend.z3_types as z3_types
import ast

r = open("tests/inference/test.py")
t = ast.parse(r.read())

analyzer = PreAnalyzer(t)


config = analyzer.get_all_configurations()
solver = z3_types.TypesSolver(config)
stubs_handler = StubsHandler()
context = Context()

stubs_handler.infer_all_files(context, solver)

for stmt in t.body:
    infer(stmt, context, solver)

solver.push()
check = solver.check(solver.assertions_vars)

try:
    model = solver.model()
    for v in sorted(context.types_map):
        z3_t = context.types_map[v]
        print("{}: {}".format(v, model[z3_t]))
except z3_types.z3types.Z3Exception as e:
    print("Check: {}".format(check))
    if check == z3_types.unsat:
        print([solver.assertions_errors[x] for x in solver.unsat_core()])
