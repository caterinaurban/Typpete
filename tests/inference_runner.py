from frontend.stmt_inferrer import *
import ast
import sys
import time

r = open("tests/inference/coop_concat.py")
t = ast.parse(r.read())
r.close()

solver = z3_types.TypesSolver(t)

context = Context()
context.type_params = solver.config.type_params
solver.infer_stubs(context, infer)

for stmt in t.body:
    infer(stmt, context, solver)

solver.push()


def print_complete_solver(z3solver):
    pp = z3_types.z3printer._PP
    pp.max_lines = 4000
    pp.max_width = 120
    formatter = z3_types.z3printer._Formatter
    formatter.max_visited = 100000
    formatter.max_depth = 50
    formatter.max_args = 512
    out = sys.stdout
    pp(out, formatter(z3solver))


start_time = time.time()

print(solver.to_smt2())

for av in solver.assertions_vars:
    print('(assert (! ' + str(av)  + ' :named named' + str(av) + '))')

# test_axiom = solver.z3_types.tvs[0] == solver.z3_types.upper(solver.z3_types.tvs[1])
# print(test_axiom)
# solver.add(test_axiom, fail_message="Just trying things")

# check = solver.optimize.check()
check = solver.check(*solver.assertions_vars)

if check == z3_types.unsat:
    print("Check: unsat")
    solver.check(solver.assertions_vars)
    print([solver.assertions_errors[x] for x in solver.unsat_core()])
else:
    # model = solver.optimize.model()
    model = solver.model()
    print(model[solver.z3_types.upper])
    for v in sorted(context.types_map):
        z3_t = context.types_map[v]

        if isinstance(z3_t, (Context, AnnotatedFunction)):
            continue

        print("{}: {}".format(v, model[z3_t]))

end_time = time.time()

print("Ran in {} seconds".format(end_time - start_time))
