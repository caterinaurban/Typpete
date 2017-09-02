from frontend.stmt_inferrer import *
from z3 import Optimize, Tactic, ParOr, ParThen
import ast
import time

r = open("/home/marco/infer_scion_types/scion/infrastructure/router/main.py")
#r = open("/home/marco/infer_scion_types/scion/lib/path_store.py")
# r = open("/home/marco/git/Typpete/unittests/inference/expressions1.py")

t = ast.parse(r.read())
r.close()

solver = z3_types.TypesSolver(t)

context = Context(t.body, solver)
solver.infer_stubs(context, infer)

for stmt in t.body:
    infer(stmt, context, solver)

solver.push()


def print_solver(z3solver):
    printer = z3_types.z3printer
    printer.set_pp_option('max_lines', 4000)
    printer.set_pp_option('max_width', 120)
    printer.set_pp_option('max_visited', 10000000)
    printer.set_pp_option('max_depth', 1000000)
    printer.set_pp_option('max_args', 512)
    printer.pp(z3solver)


def print_context(ctx, ind=""):
    for v in sorted(ctx.types_map):
        z3_t = ctx.types_map[v]
        if isinstance(z3_t, (Context, AnnotatedFunction)):
            continue
        try:
            mz3_t = model[z3_t]
        except:
            mz3_t = str(z3_t)
        print(ind + "{}: {}".format(v, mz3_t))
        if ctx.has_context_in_children(v):
            print_context(ctx.get_context_from_children(v), "\t" + ind)
        if not ind:
            print("---------------------------")
    children = False
    for child in ctx.children_contexts:
        if ctx.name == "" and child.name == "":
            children = True
            print_context(child, "\t" + ind)
    if not ind and children:
        print("---------------------------")


start_time = time.time()
print("Solving now")
#t = ParThen(Tactic("solve-eqs"), Tactic("smt"))
#s = t.solver()
#s.set("smt.mbqi", False)
#for ass in solver.all_assertions:
#    s.add(ass)
#r = s.check(*(solver.assertions_vars))
#m = s.model()

print(solver.to_smt2())
print(" ".join([str(av) for av in solver.assertions_vars]))

check = solver.optimize.check()
end_time = time.time()

if check == z3_types.unsat:
    print("Check: unsat")
    opt = Optimize(solver.ctx)
    for av in solver.assertions_vars:
        opt.add_soft(av)
    for a in solver.all_assertions:
        opt.add(a)
    checkres = opt.check()
    print(checkres)
    # uc = opt.unsat_core()
    model = opt.model()

    # for p1, p2 in return_st_pairs:
    #     print("Urgh")
    #     print(p1)
    #     print(p2)
    #     print(model.eval(p1))
    #     print(model.eval(p2))
    print_context(context)
    for av in solver.assertions_vars:
        if not model[av]:
            print("Unsat:")
            print(av)
            print(solver.assertions_errors[av])


else:
    #model = m
    model = solver.optimize.model()
    print_context(context)

print("Ran in {} seconds".format(end_time - start_time))
