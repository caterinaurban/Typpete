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

from frontend.context import Context


# noinspection PyUnresolvedReferences
def _infer_assignment_target(target, context, value_type, lineno, solver):
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
        
    TODO: Attributes assignment
    """
    if isinstance(target, ast.Name):
        if target.id in context.types_map:
            solver.add(axioms.assignment(context.get_type(target.id), value_type, solver.z3_types),
                       fail_message="Assignment in line {}".format(lineno))
        else:
            assignment_target_type = solver.new_z3_const("assign")
            solver.add(axioms.assignment(assignment_target_type, value_type, solver.z3_types),
                       fail_message="Assignment in line {}".format(lineno))
            context.set_type(target.id, assignment_target_type)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for i in range(len(target.elts)):
            target_type = solver.new_z3_const("elt_type")
            solver.add(axioms.multiple_assignment(target_type, value_type, i, solver.z3_types),
                       fail_message="Multiple assignment in line {}".format(lineno))
            _infer_assignment_target(target.elts[i], context, target_type, lineno, solver)

    elif isinstance(target, ast.Subscript):
        indexed_type = expr.infer(target.value, context, solver)
        if isinstance(target.slice, ast.Index):
            index_type = expr.infer(target.slice.value, context, solver)
            solver.add(axioms.index_assignment(indexed_type, index_type, value_type, solver.z3_types),
                       fail_message="Subscript assignment in line {}".format(lineno))
        else:  # Slice assignment
            lower_type = upper_type = step_type = z3_types.Int
            if target.slice.lower:
                lower_type = expr.infer(target.slice.lower, context, solver)
            if target.slice.upper:
                upper_type = expr.infer(target.slice.upper, context, solver)
            if target.slice.step:
                step_type = expr.infer(target.slice.step, context, solver)
            solver.add(axioms.slice_assignment(lower_type, upper_type, step_type,
                                               indexed_type, value_type, solver.z3_types),
                       fail_message="Slice assignment in line {}".format(lineno))
    elif isinstance(target, ast.Attribute):
        attr_type = expr.infer(target, context, solver)[0]
        solver.add(axioms.assignment(attr_type, value_type, solver.z3_types),
                   fail_message="Attribute assignment in line {}".format(lineno))
    else:
        raise TypeError("The inference for {} assignment is not supported.".format(type(target).__name__))


def _infer_assign(node, context, solver):
    """Infer the types of target variables in an assignment node."""

    for target in node.targets:
        _infer_assignment_target(target, context, expr.infer(node.value, context, solver), node.lineno, solver)

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

    if isinstance(node.target, ast.Name):
        solver.add(axioms.assignment(target_type, result_type, solver.z3_types),
                   fail_message="Augmented assignment in line {}".format(node.lineno))
    elif isinstance(node.target, ast.Subscript):
        indexed_type = expr.infer(node.target.value, context, solver)
        if isinstance(node.target.slice, ast.Index):
            index_type = expr.infer(node.target.slice.value, context, solver)
            solver.add(axioms.index_assignment(indexed_type, index_type, result_type, solver.z3_types),
                       fail_message="Subscript augmented assignment in line {}".format(node.lineno))
        else:
            lower_type = upper_type = step_type = z3_types.Int
            if node.target.slice.lower:
                lower_type = expr.infer(node.target.slice.lower, context, solver)
            if node.target.slice.upper:
                upper_type = expr.infer(node.target.slice.upper, context, solver)
            if node.target.slice.step:
                step_type = expr.infer(node.target.slice.step, context, solver)
            solver.add(axioms.slice_assignment(lower_type, upper_type, step_type,
                                               indexed_type, result_type, solver.z3_types),
                       fail_message="Slice augmented assignment in line {}".format(node.lineno))

    elif isinstance(node.target, ast.Attribute):
        solver.add(axioms.assignment(target_type, value_type, solver.z3_types),
                   fail_message="Augmented attribute assignment in line {}".format(node.lineno))
    return solver.z3_types.none


# noinspection PyUnresolvedReferences
def _delete_element(target, context, lineno, solver):
    """Remove (if needed) a target from the context

    Cases:
        - del var_name: remove its type mapping from the context directly.
        - del subscript:
                    * Tuple/String --> Immutable. Raise exception.
                    * List/Dict --> Do nothing to the context.
    TODO: Attribute deletion
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

        type: Union{String, Float}
    """
    body_type = _infer_body(node.body, context, node.lineno, solver)
    else_type = _infer_body(node.orelse, context, node.lineno, solver)

    if hasattr(node, "test"):
        expr.infer(node.test, context, solver)

    result_type = solver.new_z3_const("control_flow")
    solver.add(axioms.control_flow(body_type, else_type, result_type, solver.z3_types),
               fail_message="Control flow in line {}".format(node.lineno))

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

    _infer_assignment_target(node.target, context, target_type, node.lineno, solver)

    return _infer_control_flow(node, context, solver)


def _infer_with(node, context, solver):
    """Infer the types for a with block"""
    for item in node.items:
        if item.optional_vars:
            item_type = expr.infer(item.context_expr, context, solver)
            _infer_assignment_target(item.optional_vars, context, item_type, node.lineno, solver)

    return _infer_body(node.body, context, node.lineno, solver)


def _infer_try(node, context, solver):
    """Infer the types for a try/except/else block"""
    result_type = solver.new_z3_const("try")

    body_type = _infer_body(node.body, context, node.lineno, solver)
    else_type = _infer_body(node.orelse, context, node.lineno, solver)
    final_type = _infer_body(node.finalbody, context, node.lineno, solver)

    solver.add(axioms.try_except(body_type, else_type, final_type, result_type, solver.z3_types),
               fail_message="Try/Except block in line {}".format(node.lineno))

    # TODO: Infer exception handlers as classes

    for handler in node.handlers:
        handler_body_type = _infer_body(handler.body, context, handler.lineno, solver)
        solver.add(solver.z3_types.subtype(handler_body_type, result_type),
                   fail_message="Exception handler in line {}".format(handler.lineno))

    return result_type


def _init_func_context(args, context, solver):
    """Initialize the local function scope, and the arguments types"""
    local_context = Context(parent_context=context)

    # TODO starred args

    args_types = ()
    for arg in args:
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
    for i in range(len(defaults)):
        arg_idx = i + len(args_types) - len(defaults)  # The defaults array correspond to the last arguments
        default_type = expr.infer(defaults[i], context, solver)
        solver.add(solver.z3_types.subtype(default_type, args_types[arg_idx]),
                   fail_message="Function default argument in line {}".format(defaults[i].lineno))


def _infer_func_def(node, context, solver):
    """Infer the type for a function definition"""
    func_context, args_types = _init_func_context(node.args.args, context, solver)

    _infer_args_defaults(args_types, node.args.defaults, context, solver)

    return_type = _infer_body(node.body, func_context, node.lineno, solver)

    func_type = solver.z3_types.funcs[len(args_types)](args_types + (return_type,))
    result_type = solver.new_z3_const("func")
    solver.add(result_type == func_type,
               fail_message="Function definition in line {}".format(node.lineno))
    solver.add(solver.z3_types.defaults_count(result_type) == len(node.args.defaults),
               fail_message="Number of default arguments values in function definition in line {}".format(node.lineno))

    context.set_type(node.name, result_type)


def _infer_class_def(node, context, solver):
    class_context = Context(parent_context=context)
    result_type = solver.new_z3_const("class_type")
    solver.z3_types.all_types[node.name] = result_type

    for stmt in node.body:
        infer(stmt, class_context, solver)

    class_attrs = solver.z3_types.attributes[node.name]
    instance_type = solver.z3_types.classes[node.name]

    for attr in class_context.types_map:
        solver.add(class_attrs[attr] == class_context.types_map[attr],
                   fail_message="Class attribute in {}".format(node.lineno))
    class_type = solver.z3_types.type(instance_type)
    solver.add(result_type == class_type, fail_message="Class definition in line {}".format(node.lineno))
    context.set_type(node.name, result_type)


def infer(node, context, solver):
    if isinstance(node, ast.Assign):
        return _infer_assign(node, context, solver)
    elif isinstance(node, ast.AugAssign):
        return _infer_augmented_assign(node, context, solver)
    elif isinstance(node, ast.Return):
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
    return solver.z3_types.none
