from frontend.pre_analysis import PreAnalyzer
from frontend.stmt_inferrer import *
from frontend.stubs.stubs_handler import StubsHandler
import frontend.z3_types as z3_types
import ast
import sys

r = open("tests/inference/test.py")
t = ast.parse(r.read())
r.close()


analyzer = PreAnalyzer(t, "tests/inference")
stubs_handler = StubsHandler(analyzer)


config = analyzer.get_all_configurations()
solver = z3_types.TypesSolver(config)

context = Context()

stubs_handler.infer_all_files(context, solver, config.used_names)

for stmt in t.body:
    infer(stmt, context, solver)

solver.push()


def print_complete_solver(solver):
    pp = z3_types.z3printer._PP
    pp.max_lines = 4000
    pp.max_width = 120
    formatter = z3_types.z3printer._Formatter
    formatter.max_visited = 100000
    formatter.max_depth = 50
    formatter.max_args = 512
    out = sys.stdout
    pp(out, formatter(solver))


check = solver.check(solver.assertions_vars)
# print_complete_solver(solver)
try:
    model = solver.model()
    for v in sorted(context.types_map):
        z3_t = context.types_map[v]

        if isinstance(z3_t, Context):
            continue

        print("{}: {}".format(v, model[z3_t]))
except z3_types.z3types.Z3Exception as e:
    print("Check: {}".format(check))
    if check == z3_types.unsat:
        print([solver.assertions_errors[x] for x in solver.unsat_core()])
