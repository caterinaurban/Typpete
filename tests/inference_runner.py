from frontend.stmt_inferrer import *
from frontend.import_handler import ImportHandler
from frontend.config import config
from z3 import Optimize

import ast
import os
import time
import astunparse
import sys
sys.setrecursionlimit(10000)

start_time = time.time()
base_folder = 'tests/imp'
file_name = 'imp'

class_type_params = None
type_params = None

t = ImportHandler.get_module_ast(file_name, base_folder)

solver = z3_types.TypesSolver(t, base_folder=base_folder, type_params=type_params, class_type_params=class_type_params)

context = Context(t, t.body, solver)
context.type_params = solver.config.type_params
context.class_type_params = solver.config.class_type_params
solver.infer_stubs(context, infer)

for stmt in t.body:
    infer(stmt, context, solver, t)

end_time = time.time()
print("Constraints collection took  {}s".format(end_time - start_time))

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

print_solver(solver)

start_time = time.time()
if config['enable_soft_constraints']:
    check = solver.optimize.check()
else:
    check = solver.check(solver.assertions_vars)
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
    for av in solver.assertions_vars:
        if not model[av]:
            print("Unsat:")
            print(solver.assertions_errors[av])
else:
    if config['enable_soft_constraints']:
        model = solver.optimize.model()
    else:
        model = solver.model()

context.generate_typed_ast(model, solver)

# uncomment this to write typed source into a file
write_path = "inference_output/" + base_folder
print("Output is written to {}".format(write_path))
if not os.path.exists(write_path):
    os.makedirs(write_path)
write_path += '/' + file_name + '.py'
if not os.path.exists(os.path.dirname(write_path)):
    os.makedirs(os.path.dirname(write_path))
file = open(write_path, 'w')
file.write(astunparse.unparse(t))
file.close()

ImportHandler.write_to_files(model, solver)


print("Constraints solving took  {}s".format(end_time - start_time))
