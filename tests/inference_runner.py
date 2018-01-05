from frontend.stmt_inferrer import *
from z3 import Optimize, Const
import ast
import time
import astunparse

# file_path = "/home/marco/infer_scion_types/Typpete/tests/adventure/data.py"
file_path = "unittests/inference/coop_concatenate.py"
file_name = file_path.split("/")[-1]

r = open(file_path)

t = ast.parse(r.read())
r.close()

solver = z3_types.TypesSolver(t)

context = Context(t.body, solver)
context.type_params = solver.config.type_params
context.class_type_params = solver.config.class_type_params
solver.infer_stubs(context, infer)

for stmt in t.body:
    infer(stmt, context, solver, t)

solver.push()


def print_solver(z3solver):
    printer = z3_types.z3printer
    printer.set_pp_option('max_lines', 4000)
    printer.set_pp_option('max_width', 120)
    printer.set_pp_option('max_visited', 10000000)
    printer.set_pp_option('max_depth', 1000000)
    printer.set_pp_option('max_args', 512)
    printer.pp(z3solver)

def print_model():
    printer = z3_types.z3printer
    printer.set_pp_option('max_lines', 4000)
    printer.set_pp_option('max_width', 120)
    printer.set_pp_option('max_visited', 10000000)
    printer.set_pp_option('max_depth', 1000000)
    printer.set_pp_option('max_args', 512)
    printer.pp(model)


def print_context(ctx, ind=""):
    for v in sorted(ctx.types_map):
        z3_t = ctx.types_map[v]
        if isinstance(z3_t, (Context, AnnotatedFunction)):
            continue
        try:
            t = model[z3_t]
            print(ind + "{}: {}".format(v, t if t is not None else z3_t))
        except z3_types.Z3Exception:
            print(ind + "{}: {}".format(v, z3_t))
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

# print(solver)
start_time = time.time()
check = solver.optimize.check()
end_time = time.time()

if check == z3_types.unsat:
    print("Check: unsat")
    opt = Optimize(solver.ctx)
    for av in solver.assertions_vars:
        opt.add_soft(av)
    for a in solver.all_assertions:
        opt.add(a)
    for a in solver.z3_types.subtyping:
        opt.add(a)
    for a in solver.z3_types.subst_axioms:
        opt.add(a)
    for a in solver.forced:
        opt.add(a)
    checkres = opt.check()
    model = opt.model()
    print_context(context)
    for av in solver.assertions_vars:
        if not model[av]:
            print("Unsat:")
            print(solver.assertions_errors[av])
else:
    model = solver.optimize.model()
    context.generate_typed_ast(model, solver)
    print_model()

    # uncomment this to write typed source into a file
    # write_path = "inference_output/" + file_name
    # file = open(write_path, 'w')
    # file.write(astunparse.unparse(t))
    # file.close()
    print(astunparse.unparse(t))


print("Ran in {} seconds".format(end_time - start_time))
