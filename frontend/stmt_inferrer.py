"""Inferrer for python statements.

Infers the types for the following expressions:
    - Assign(expr* targets, expr value)
    - AugAssign(expr target, operator op, expr value)
    - Return(expr? value)
    - Delete(expr* targets)
    - If(expr test, stmt* body, stmt* orelse)
    - While(expr test, stmt* body, stmt* orelse)
    - For(expr target, expr iter, stmt* body, stmt* orelse)
    - AsyncFor(expr target, expr iter, stmt* body, stmt* orelse)
    - With(withitem* items, stmt* body)
    - AsyncWith(withitem* items, stmt* body)
    - Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)

    TODO:
    - Import(alias* names)
    - ImportFrom(identifier? module, alias* names, int? level)
    - Global(identifier* names)
    - Nonlocal(identifier* names)
"""

import ast
import frontend.expr_inferrer as expr
import frontend.z3_axioms as axioms
import frontend.z3_types as z3_types
import sys

from frontend.config import config as inference_config
from frontend.context import Context, AnnotatedFunction
from frontend.import_handler import ImportHandler


def _infer_one_target(target, context, solver):
    """
    Get the type of the left hand side of an assignment
    
    :param target: The target on the left hand side 
    :param context: The current context level
    :param solver: The SMT solver
    :return: the type of the target
    """
    if isinstance(target, ast.Name):
        if target.id in context.types_map:
            return context.get_type(target.id)
        else:
            target_type = solver.new_z3_const("assign")
            context.set_type(target.id, target_type)
            return target_type
    elif isinstance(target, ast.Tuple):
        args_types = []
        for elt in target.elts:
            args_types.append(_infer_one_target(elt, context, solver))
        return solver.z3_types.tuples[len(args_types)](*args_types)
    elif isinstance(target, ast.List):
        list_type = solver.new_z3_const("assign")
        for elt in target.elts:
            solver.add(list_type == _infer_one_target(elt, context, solver),
                       fail_message="List assignment in line {}".format(target.lineno))
        return solver.z3_types.list(list_type)
    target_type = expr.infer(target, context, solver)

    if isinstance(target, ast.Subscript):
        solver.add(axioms.subscript_assignment(expr.infer(target.value, context, solver), solver.z3_types),
                   fail_message="Subscript assignment in line {}".format(target.lineno))

    return target_type


def _infer_assignment_target(target, context, value_type, solver):
    """Infer the type of a target in an assignment

    Attributes:
        target: the target whose type is to be inferred
        context: the current context level
        value_type: the type of the value assigned to the target

    Target cases:
        - Variable name. Ex: x = 1
        - Tuple. Ex: a, b = 1, "string"
        - List. Ex: [a, b] = [1, "string"]
        - Subscript. Ex: x[0] = 1, x[1 : 2] = [2,3], x["key"] = value
        - Compound: Ex: a, b[0], [c, d], e["key"] = 1, 2.0, [True, False], "value"
    """
    target_type = _infer_one_target(target, context, solver)
    solver.add(axioms.assignment(target_type, value_type, solver.z3_types),
               fail_message="Assignment in line {}".format(target.lineno))
    solver.optimize.add_soft(target_type == value_type)


def _is_type_var_declaration(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "TypeVar"


def _infer_assign(node, context, solver):
    """Infer the types of target variables in an assignment node."""

    if _is_type_var_declaration(node.value):
        solver.annotation_resolver.add_type_var(node.targets[0], node.value)
    else:
        for target in node.targets:
            _infer_assignment_target(target, context, expr.infer(node.value, context, solver), solver)

    return solver.z3_types.none


def _infer_augmented_assign(node, context, solver):
    """Infer the types for augmented assignments

    Examples:
        a += 5
        b[2] &= x
        c.x -= f(1, 2)
    """
    target_type = expr.infer(node.target, context, solver)
    value_type = expr.infer(node.value, context, solver)
    result_type = expr.binary_operation_type(target_type, node.op, value_type, node.lineno, solver)

    _infer_assignment_target(node.target, context, result_type, solver)

    return solver.z3_types.none


# noinspection PyUnresolvedReferences
def _delete_element(target, context, lineno, solver):
    """Remove (if needed) a target from the context

    Cases:
        - del var_name: remove its type mapping from the context directly.
        - del subscript:
                    * Tuple/String --> Immutable. Raise exception.
                    * List/Dict --> Do nothing to the context.
    """
    if isinstance(target, (ast.Tuple, ast.List)):  # Multiple deletions
        for elem in target.elts:
            _delete_element(elem, context, lineno, solver)
    elif isinstance(target, ast.Name):
        context.delete_type(target.id)
    elif isinstance(target, ast.Subscript):
        expr.infer(target, context, solver)
        indexed_type = expr.infer(target.value, context, solver)
        solver.add(axioms.delete_subscript(indexed_type, solver.z3_types),
                   fail_message="Deletion in line {}".format(lineno))
    elif isinstance(target, ast.Attribute):
        raise NotImplementedError("Attribute deletion is not supported.")


def _infer_delete(node, context, solver):
    """Remove (if needed) the type of the deleted items in the current context"""
    for target in node.targets:
        _delete_element(target, context, node.lineno, solver)

    return solver.z3_types.none


def _infer_body(body, context, lineno, solver):
    """Infer the type of a code block containing multiple statements"""
    body_type = solver.new_z3_const("body")
    if len(body) == 0:
        solver.add(body_type == solver.z3_types.none,
                   fail_message="Body type in line {}".format(lineno))
        return body_type
    stmts_types = []
    for stmt in body:
        stmt_type = infer(stmt, context, solver)
        stmts_types.append(stmt_type)
        solver.add(axioms.body(body_type, stmt_type, solver.z3_types),
                   fail_message="Body type in line {}".format(lineno))
    # The body type should be none if all statements have none type.
    solver.add(z3_types.Implies(z3_types.And([x == solver.z3_types.none for x in stmts_types]),
                                body_type == solver.z3_types.none),
               fail_message="Body type in line {}".format(lineno))

    return body_type


def _infer_control_flow(node, context, solver):
    """Infer the type(s) for an if/while/for statements block.

    Arguments:
        node: The AST node to be inferred
        context: the current context level
    Example:
        if (some_condition):
            ......
            return "some string"
        else:
            ......
            return 2.0

        type: super{String, Float}
    """
    body_context = Context(parent_context=context)
    else_context = Context(parent_context=context)

    body_type = _infer_body(node.body, body_context, node.lineno, solver)
    else_type = _infer_body(node.orelse, else_context, node.lineno, solver)

    # Re-assigning variables in the body branch
    for v in body_context.types_map:
        if context.has_variable(v):
            t1 = body_context.types_map[v]
            t2 = context.get_type(v)
            solver.add(t1 == t2,
                       fail_message="re-assigning in flow branching in line {}".format(node.lineno))

    # Re-assigning variables in the else branch
    for v in else_context.types_map:
        if context.has_variable(v):
            t1 = else_context.types_map[v]
            t2 = context.get_type(v)
            solver.add(t1 == t2,
                       fail_message="re-assigning in flow branching in line {}".format(node.lineno))

    # Take intersection of variables in both contexts
    for v in body_context.types_map:
        if v in else_context.types_map and not context.has_variable(v):
            var_type = solver.new_z3_const("branching_var")
            t1 = body_context.types_map[v]
            t2 = else_context.types_map[v]

            if inference_config["enforce_same_type_in_branches"]:
                branch_axioms = [t1 == var_type, t2 == var_type]
            else:
                branch_axioms = [solver.z3_types.subtype(t1, var_type), solver.z3_types.subtype(t2, var_type)]

            solver.add(branch_axioms,
                       fail_message="subtyping in flow branching in line {}".format(node.lineno))

            solver.optimize.add_soft(t1 == var_type)
            solver.optimize.add_soft(t2 == var_type)
            context.set_type(v, var_type)

    if hasattr(node, "test"):
        expr.infer(node.test, context, solver)

    result_type = solver.new_z3_const("control_flow")
    solver.add(axioms.control_flow(body_type, else_type, result_type, solver.z3_types),
               fail_message="Control flow in line {}".format(node.lineno))
    solver.optimize.add_soft(result_type == body_type)
    solver.optimize.add_soft(result_type == else_type)
    return result_type


def _infer_for(node, context, solver):
    """Infer the type for a for loop node

    Limitation:
        - The iterable can't be a tuple.
            For example: the following is not allowed:
                for x in (1, 2.0, "string"):
                    ....
    """
    iter_type = expr.infer(node.iter, context, solver)

    # Infer the target in the loop, inside the global context
    # Cases:
    # - Var name. Ex: for i in range(5)..
    # - Tuple. Ex: for (a,b) in [(1,"st"), (3,"st2")]..
    # - List. Ex: for [a,b] in [(1, "st"), (3, "st2")]..
    target_type = solver.new_z3_const("for_target")
    solver.add(axioms.for_loop(iter_type, target_type, solver.z3_types),
               fail_message="For loop in line {}".format(node.lineno))

    _infer_assignment_target(node.target, context, target_type, solver)

    return _infer_control_flow(node, context, solver)


def _infer_with(node, context, solver):
    """Infer the types for a with block"""
    for item in node.items:
        if item.optional_vars:
            item_type = expr.infer(item.context_expr, context, solver)
            _infer_assignment_target(item.optional_vars, context, item_type, solver)

    return _infer_body(node.body, context, node.lineno, solver)


def _infer_try(node, context, solver):
    """Infer the types for a try/except/else block"""
    result_type = solver.new_z3_const("try")

    body_type = _infer_body(node.body, context, node.lineno, solver)
    else_type = _infer_body(node.orelse, context, node.lineno, solver)
    final_type = _infer_body(node.finalbody, context, node.lineno, solver)

    solver.add(axioms.try_except(body_type, else_type, final_type, result_type, solver.z3_types),
               fail_message="Try/Except block in line {}".format(node.lineno))
    solver.optimize.add_soft(result_type == body_type)
    solver.optimize.add_soft(result_type == else_type)
    solver.optimize.add_soft(result_type == final_type)

    # TODO: Infer exception handlers as classes

    for handler in node.handlers:
        handler_body_type = _infer_body(handler.body, context, handler.lineno, solver)
        solver.add(solver.z3_types.subtype(handler_body_type, result_type),
                   fail_message="Exception handler in line {}".format(handler.lineno))

    return result_type


def _init_func_context(name, args, context, solver):
    """Initialize the local function scope, and the arguments types"""
    local_context = Context(name=name, parent_context=context)

    # TODO starred args

    args_types = ()
    for arg in args:
        if arg.annotation:
            arg_type = solver.resolve_annotation(arg.annotation)
        else:
            arg_type = solver.new_z3_const("func_arg")
        local_context.set_type(arg.arg, arg_type)
        args_types = args_types + (arg_type,)

    return local_context, args_types


def _infer_args_defaults(args_types, defaults, context, solver):
    """Infer the default values of function arguments (if any)
    
    :param args_types: Z3 constants for arguments types
    :param defaults: AST nodes for default values of arguments
    :param context: The parent of the function context
    :param solver: The inference Z3 solver
    
    
    A default array of length `n` represents the default values of the last `n` arguments
    """
    for i, default in enumerate(defaults):
        arg_idx = i + len(args_types) - len(defaults)  # The defaults array correspond to the last arguments
        default_type = expr.infer(default, context, solver)
        solver.add(solver.z3_types.subtype(default_type, args_types[arg_idx]),
                   fail_message="Function default argument in line {}".format(defaults[i].lineno))
        solver.optimize.add_soft(default_type == args_types[arg_idx])


def is_annotated(node):
    """Check the arguments and return are annotated in a function definition"""
    if not node.returns:
        return False
    for arg in node.args.args:
        if not arg.annotation:
            return False
    return True


def is_stub(node):
    """Check if the function is a stub definition:
    
    For the function to be a stub, it should be fully annotated and should have no body.
    The body should be a single `Pass` statement with optional docstring.
    """
    if not is_annotated(node):
        return False

    return ((len(node.body) == 1 and isinstance(node.body[0], ast.Pass))
            or (len(node.body) == 2 and isinstance(node.body[0], ast.Expr) and isinstance(node.body[1], ast.Pass)))


def has_type_var(node, solver):
    """Check if the function definition has a generic type variable annotation
    
    Inspect all the nodes of the type annotations and look for relevant generic type vars
    """
    found_type_var = False

    # Get annotations of args and return in one list
    all_annotations = []
    if node.returns:
        all_annotations.append(node.returns)

    for arg in node.args.args:
        if arg.annotation:
            all_annotations.append(arg.annotation)

    # check if any annotation has a type variable
    for annotation in all_annotations:
        if found_type_var:
            break
        # walk over all nodes because the type variable might be deep inside.
        # example: Tuple[List[str], Dict[T, str]]
        all_annotation_nodes = list(ast.walk(annotation))
        for n in all_annotation_nodes:
            # check all nodes which are instance of ast.Name; they are the only candidates for type vars
            if isinstance(n, ast.Name) and n.id in solver.annotation_resolver.type_var_poss:
                found_type_var = True
                break
    if found_type_var:
        if len(all_annotations) < len(node.args.args) + 1:
            raise TypeError("Function {} in line {} containing type variables should be fully annotated."
                            .format(node.name, node.lineno))

    return found_type_var


def _infer_func_def(node, context, solver):
    """Infer the type for a function definition"""
    if is_stub(node) or has_type_var(node, solver):
        return_annotation = node.returns
        args_annotations = []
        for arg in node.args.args:
            args_annotations.append(arg.annotation)
        defaults_count = len(node.args.defaults)
        if hasattr(node, "method_type"):  # check if the node contains the manually added method flag
            if node.method_type not in context.builtin_methods:
                context.builtin_methods[node.method_type] = {}
            context.builtin_methods[node.method_type][node.name] = AnnotatedFunction(args_annotations,
                                                                                     return_annotation,
                                                                                     defaults_count)
        else:
            context.set_type(node.name, AnnotatedFunction(args_annotations, return_annotation, defaults_count))
        return

    func_context, args_types = _init_func_context(node.name, node.args.args, context, solver)
    result_type = solver.new_z3_const("func")
    result_type.args_count = len(node.args.args)
    context.set_type(node.name, result_type)

    if hasattr(node.args, "defaults"):
        # Use the default args to infer the function parameters
        _infer_args_defaults(args_types, node.args.defaults, context, solver)
        defaults_len = len(node.args.defaults)
    else:
        defaults_len = 0

    if node.returns:
        return_type = solver.resolve_annotation(node.returns)
        if inference_config["ignore_fully_annotated_function"] and is_annotated(node):
            body_type = return_type
        else:
            body_type = _infer_body(node.body, func_context, node.lineno, solver)
        solver.add(body_type == return_type,
                   fail_message="Return type annotation in line {}".format(node.lineno))
    else:
        body_type = _infer_body(node.body, func_context, node.lineno, solver)

    func_type = solver.z3_types.funcs[len(args_types)]((defaults_len,) + args_types + (body_type,))
    solver.add(result_type == func_type,
               fail_message="Function definition in line {}".format(node.lineno))


def _infer_class_def(node, context, solver):
    class_context = Context(name=node.name, parent_context=context)
    result_type = solver.new_z3_const("class_type")
    solver.z3_types.all_types[node.name] = result_type

    for stmt in node.body:
        infer(stmt, class_context, solver)

    class_attrs = solver.z3_types.instance_attributes[node.name]
    instance_type = solver.z3_types.classes[node.name]

    for attr in class_context.types_map:
        solver.add(class_attrs[attr] == class_context.types_map[attr],
                   fail_message="Class attribute in {}".format(node.lineno))

    # Set the type of the first arg in the class methods to be instance of this class
    # TODO check staticmethod decorator
    for func_name, args_count in solver.config.class_to_funcs[node.name]:
        func_type = class_context.get_type(func_name)
        arg_accessor = getattr(solver.z3_types.type_sort, "func_{}_arg_1".format(args_count))
        solver.add(arg_accessor(func_type) == instance_type,
                   fail_message="First arg in class methods has class instance type")

    class_type = solver.z3_types.type(instance_type)
    solver.add(result_type == class_type, fail_message="Class definition in line {}".format(node.lineno))
    result_type.is_class = True
    context.set_type(node.name, result_type)


def _infer_import(node, context, solver):
    """Infer the imported module in normal import statement
    
    The imported modules can be used with direct module access only.
    Which means, re-assigning the module to a variable or passing it as a function arg is not supported.
    
    For example, the following is not possible:
        - import X
          x = X
          
        - import X
          f(X)
          
    The importing supports deep module access. For example, the following is supported.
    
    >> A.py
    x = 1
    
    >> B.py
    import A
    
    >> C.py
    import B
    
    print(B.A.x)
    """
    for name in node.names:
        import_context = ImportHandler.infer_import(name.name, solver.config.base_folder, infer, solver)

        if name.asname:
            # import X as Y
            module_name = name.asname
        else:
            module_name = name.name

        # Store the module context in the current context.
        context.set_type(module_name, import_context)

    return solver.z3_types.none


def _infer_import_from(node, context, solver):
    """Infer the imported module in an `import from` statement"""
    if node.module == "typing":
        # FIXME ignore typing module for now, so as not to break type variables
        # Remove after implementing stub for typing and built-in importing
        return solver.z3_types.none
    import_context = ImportHandler.infer_import(node.module, solver.config.base_folder, infer, solver)

    if len(node.names) == 1 and node.names[0].name == "*":
        # import all module elements
        for v in import_context.types_map:
            context.set_type(v, import_context.get_type(v))
    else:
        # Import only stated names
        for name in node.names:
            elt_name = name.name
            if name.asname:
                elt_name = name.asname
            if name.name not in import_context.types_map:
                raise ImportError("Cannot import name {}".format(name.name))
            context.set_type(elt_name, import_context.get_type(name.name))

    return solver.z3_types.none


def infer(node, context, solver):
    if isinstance(node, ast.Assign):
        return _infer_assign(node, context, solver)
    elif isinstance(node, ast.AugAssign):
        return _infer_augmented_assign(node, context, solver)
    elif isinstance(node, ast.Return):
        if not node.value:
            return solver.z3_types.none
        return expr.infer(node.value, context, solver)
    elif isinstance(node, ast.Delete):
        return _infer_delete(node, context, solver)
    elif isinstance(node, (ast.If, ast.While)):
        return _infer_control_flow(node, context, solver)
    elif isinstance(node, ast.For):
        return _infer_for(node, context, solver)
    elif sys.version_info[0] >= 3 and sys.version_info[1] >= 5 and isinstance(node, ast.AsyncFor):
        # AsyncFor is introduced in Python 3.5
        return _infer_for(node, context, solver)
    elif isinstance(node, ast.With):
        return _infer_with(node, context, solver)
    elif sys.version_info[0] >= 3 and sys.version_info[1] >= 5 and isinstance(node, ast.AsyncWith):
        # AsyncWith is introduced in Python 3.5
        return _infer_with(node, context, solver)
    elif isinstance(node, ast.Try):
        return _infer_try(node, context, solver)
    elif isinstance(node, ast.FunctionDef):
        return _infer_func_def(node, context, solver)
    elif isinstance(node, ast.ClassDef):
        return _infer_class_def(node, context, solver)
    elif isinstance(node, ast.Expr):
        expr.infer(node.value, context, solver)
    elif isinstance(node, ast.Import):
        return _infer_import(node, context, solver)
    elif isinstance(node, ast.ImportFrom):
        return _infer_import_from(node, context, solver)
    return solver.z3_types.none
