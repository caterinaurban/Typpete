from typpete.src.stmt_inferrer import *
from typpete.src.import_handler import ImportHandler
import typpete.src.config as config
from z3 import Optimize

import os
import time
import astunparse
import sys


def configure_inference(flags):
    class_type_params = None
    func_type_params = None
    for flag in flags:
        flag_assignment = flag[2:]
        try:
            flag_name, flag_value = flag_assignment.split('=')
        except ValueError:
            print("Invalid flag assignment {}".format(flag_assignment))
            continue
        # func_type_params=make_object,1,d,2
        if flag_name == 'func_type_params':
            if func_type_params is None:
                func_type_params = {}
            flag_value = flag_value.split(',')
            for i in range(0, len(flag_value), 2):
                func_name = flag_value[i]
                count = int(flag_value[i + 1])
                type_vars = ['{}{}'.format(func_name, i) for i in range(count)]
                func_type_params[func_name] = type_vars
        elif flag_name == 'class_type_params':
            if class_type_params is None:
                class_type_params = {}
            flag_value = flag_value.split(',')
            for i in range(0, len(flag_value), 2):
                cls_name = flag_value[i]
                count = int(flag_value[i + 1])
                type_vars = ['{}{}'.format(cls_name, i) for i in range(count)]
                class_type_params[cls_name] = type_vars
        elif flag_name in config.config:
            config.config[flag_name] = flag_value == 'True'
        else:
            print("Invalid flag {}. Ignoring.".format(flag_name))
    return class_type_params, func_type_params


def print_help():
    options = ["ignore_fully_annotated_function",
               "enforce_same_type_in_branches",
               "allow_attributes_outside_init",
               "none_subtype_of_all",
               "enable_soft_constraints",
               "func_type_params",
               "class_type_params"]
    descriptions = ["Whether to ignore the body of fully annotated functions"
                    " and just take the provided types for args/return.",
                    "Whether to allow different branches to use different types of same variable.",
                    "Whether to allow to de- fine instance attribute outside __init__.",
                    "Whether to make None a sub-type of all types.",
                    "Whether to use soft con- straints to infer more precise types for local variables.",
                    "Type parameters required by generic functions.",
                    "Type parameters required by generic classes."]

    print("Typpete: Static type inference for Python 3")
    print("Usage:")
    print("\ttyppete file_path [working_directory] [options]")
    print()
    print("Options:")
    for i, option in enumerate(options):
        print("\t--{}:\t{}".format(option, descriptions[i]))


def run_inference(file_name=None, base_folder=None):
    if not file_name:
        if len(sys.argv) >= 2 and sys.argv[1] != '--help':
            file_name = sys.argv[1]
            if len(sys.argv) >= 3:
                base_folder = sys.argv[2]
        else:
            print_help()
            return
    start_time = time.time()
    class_type_params, func_type_params = configure_inference([flag for flag in sys.argv[2:] if flag.startswith("--")])

    if not base_folder:
        base_folder = ''

    if file_name.endswith('.py'):
        file_name = file_name[:-3]

    t = ImportHandler.get_module_ast(file_name, base_folder)

    solver = z3_types.TypesSolver(t, base_folder=base_folder, type_params=func_type_params,
                                  class_type_params=class_type_params)

    context = Context(t, t.body, solver)
    context.type_params = solver.config.type_params
    context.class_type_params = solver.config.class_type_params
    solver.infer_stubs(context, infer)

    for stmt in t.body:
        infer(stmt, context, solver)

    solver.push()
    end_time = time.time()
    print("Constraints collection took  {}s".format(end_time - start_time))

    start_time = time.time()
    if config.config['enable_soft_constraints']:
        check = solver.optimize.check()
    else:
        check = solver.check(solver.assertions_vars)
    end_time = time.time()
    print("Constraints solving took  {}s".format(end_time - start_time))

    write_path = "inference_output/" + base_folder
    print("Writing output to {}".format(write_path))
    if not os.path.exists(write_path):
        os.makedirs(write_path)

    if write_path.endswith('/'):
        write_path = write_path[:-1]

    file = open(write_path + '/{}_constraints_log.txt'.format(file_name.replace('/', '.')), 'w')
    file.write(print_solver(solver))
    file.close()

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
        if config.config['enable_soft_constraints']:
            model = solver.optimize.model()
        else:
            model = solver.model()

        context.generate_typed_ast(model, solver)
        ImportHandler.add_required_imports(file_name, t, context)

        write_path += '/' + file_name + '.py'

        if not os.path.exists(os.path.dirname(write_path)):
            os.makedirs(os.path.dirname(write_path))
        file = open(write_path, 'w')
        file.write(astunparse.unparse(t))
        file.close()

        ImportHandler.write_to_files(model, solver)

def print_solver(z3solver):
    printer = z3_types.z3printer
    printer.set_pp_option('max_lines', 4000)
    printer.set_pp_option('max_width', 1000)
    printer.set_pp_option('max_visited', 10000000)
    printer.set_pp_option('max_depth', 1000000)
    printer.set_pp_option('max_args', 512)
    return str(z3solver)


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
            print_context(ctx.get_context_from_children(v), model, "\t" + ind)
        if not ind:
            print("---------------------------")
    children = False
    for child in ctx.children_contexts:
        if ctx.name == "" and child.name == "":
            children = True
            print_context(child, model, "\t" + ind)
    if not ind and children:
        print("---------------------------")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        base_folder = sys.argv[2] if len(sys.argv) >= 3 else None
        run_inference(file_path, base_folder)
    else:
        print_help()
