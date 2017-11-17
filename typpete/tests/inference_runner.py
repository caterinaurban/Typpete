from typpete.frontend.stmt_inferrer import *
import typpete.frontend.config as config
import ast
import time
import astunparse
import sys


def configure_inference(flags):
    for flag in flags:
        flag_assignment = flag[2:]
        try:
            flag_name, flag_value = flag_assignment.split('=')
        except ValueError:
            print("Invalid flag assignment {}".format(flag_assignment))
            continue
        if flag_name in config.config:
            config.config[flag_name] = flag_value == 'True'
        else:
            print("Invalid flag {}. Ignoring.".format(flag_name))

def run_inference(file_path=None):
    if not file_path:
        try:
            file_path = sys.argv[1]
        except:
            print("Please specify the python file")
            return

    configure_inference([flag for flag in sys.argv[2:] if flag.startswith("--")])

    root_folder = '/'.join(file_path.split('/')[:-1])

    r = open(file_path)
    t = ast.parse(r.read())
    r.close()

    solver = z3_types.TypesSolver(t, root_folder)

    context = Context(t.body, solver)
    solver.infer_stubs(context, infer)

    for stmt in t.body:
        infer(stmt, context, solver)

    solver.push()

    start_time = time.time()
    check = solver.optimize.check()
    end_time = time.time()

    if check == z3_types.unsat:
        print("Check: unsat")
        solver.check(solver.assertions_vars)
        print(solver.unsat_core())
        print([solver.assertions_errors[x] for x in solver.unsat_core()])
    else:
        model = solver.optimize.model()
        context.generate_typed_ast(model, solver)

        # uncomment this to write typed source into a file
        # write_path = "inference_output/" + file_name
        # file = open(write_path, 'w')
        # file.write(astunparse.unparse(t))
        # file.close()
        print(astunparse.unparse(t))

    print("Ran in {} seconds".format(end_time - start_time))

def print_solver(z3solver):
    printer = z3_types.z3printer
    printer.set_pp_option('max_lines', 4000)
    printer.set_pp_option('max_width', 120)
    printer.set_pp_option('max_visited', 10000000)
    printer.set_pp_option('max_depth', 1000000)
    printer.set_pp_option('max_args', 512)
    printer.pp(z3solver)


def print_context(ctx, model, ind=""):
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

if __name__ == '__main__':
    try:
        file_path = sys.argv[1]
        run_inference(file_path)
    except:
        print("Please specify the python file")
