"""Inference for python expressions.

Infers the types for the following expressions:
    - BinOp(expr left, operator op, expr right)
    - UnaryOp(unaryop op, expr operand)
    - Dict(expr* keys, expr* values)
    - Set(expr* elts)
    - Num(object n)
    - Str(string s)
    - NameConstant(singleton value)
    - List(expr* elts, expr_context ctx)
    - Tuple(expr* elts, expr_context ctx)
    - Bytes(bytes s)
    - IfExp(expr test, expr body, expr orelse)
    - Subscript(expr value, slice slice, expr_context ctx)
    - Await(expr value) --> Python 3.5+
    - Yield(expr? value)
    - Compare(expr left, cmpop* ops, expr* comparators)
    - Name(identifier id, expr_context ctx)
    - FormattedValue(expr value, int? conversion, expr? format_spec) --> Python 3.6+
    - JoinedStr(expr* values) --> Python 3.6+
    - ListComp(expr elt, comprehension* generators)
    - SetComp(expr elt, comprehension* generators)
    - DictComp(expr key, expr value, comprehension* generators)
    - Attribute(expr value, identifier attr, expr_context ctx)

TODO:
    - Lambda(arguments args, expr body)
    - GeneratorExp(expr elt, comprehension* generators)
    - YieldFrom(expr value)
    - Starred(expr value, expr_context ctx)
"""

import ast
import frontend.z3_types as z3_types
import frontend.z3_axioms as axioms
import sys

from frontend.context import Context


def infer_numeric(node):
    """Infer the type of a numeric node"""
    if type(node.n) == int:
        return z3_types.Int
    if type(node.n) == float:
        return z3_types.Float
    if type(node.n) == complex:
        return z3_types.Complex


def _get_elements_type(elts, context, lineno):
    """Return the elements type of a collection"""
    elts_type = z3_types.new_z3_const("elts")
    if len(elts) == 0:
        return elts_type
    for i in range(0, len(elts)):
        cur_type = infer(elts[i], context)
        z3_types.solver.add(cur_type == elts_type, fail_message="List literal in line {}".format(lineno))

    return elts_type


def infer_list(node, context):
    """Infer the type of a homogeneous list

    Returns: TList(Type t), where t is the type of the list elements
    """
    return z3_types.List(_get_elements_type(node.elts, context, node.lineno))


def infer_dict(node, context):
    """Infer the type of a dictionary with homogeneous key set and value set

    Returns: TDictionary(Type k_t, Type v_t), where:
            k_t is the type of dictionary keys
            v_t is the type of dictionary values
    """
    keys_type = _get_elements_type(node.keys, context, node.lineno)
    values_type = _get_elements_type(node.values, context, node.lineno)
    return z3_types.Dict(keys_type, values_type)


def infer_tuple(node, context):
    """Infer the type of a tuple

    Returns: TTuple(Type[] t), where t is a list of the tuple's elements types
    """
    tuple_types = ()
    for elem in node.elts:
        elem_type = infer(elem, context)
        tuple_types = tuple_types + (elem_type,)

    # Instantiate the correct z3 tuple type based on length of tuple elements:
    # len(tuple_types) == 1 --> Tuple1(tuple_types)
    # len(tuple_types) == 2 --> Tuple2(tuple_types)
    # .....
    # len(tuple_types) == 5 --> Tuple5(tuple_types)

    if len(tuple_types) == 0:
        return z3_types.Tuples[0]

    return z3_types.Tuples[len(tuple_types)](tuple_types)


def infer_name_constant(node):
    """Infer the type of name constants like: True, False, None"""
    if isinstance(node.value, bool):
        return z3_types.Bool
    elif node.value is None:
        return z3_types.zNone
    raise NotImplementedError("The inference for {} is not supported.".format(node.value))


def infer_set(node, context):
    """Infer the type of a homogeneous set

    Returns: TSet(Type t), where t is the type of the set elements
    """
    return z3_types.Set(_get_elements_type(node.elts, context, node.lineno))


def _infer_add(left_type, right_type, lineno):
    """Infer the type of an addition operation, and add the corresponding axioms"""
    result_type = z3_types.new_z3_const("addition_result")
    z3_types.solver.add(axioms.add(left_type, right_type, result_type),
                        fail_message="Addition in line {}".format(lineno))
    return result_type


def _infer_mult(left_type, right_type, lineno):
    """Infer the type of a multiplication operation, and add the corresponding axioms"""
    result_type = z3_types.new_z3_const("multiplication_result")
    z3_types.solver.add(axioms.mult(left_type, right_type, result_type),
                        fail_message="Multiplication in line {}".format(lineno))
    return result_type


def _infer_div(left_type, right_type, lineno):
    """Infer the type of a division operation, and add the corresponding axioms"""
    result_type = z3_types.new_z3_const("division_result")
    z3_types.solver.add(axioms.div(left_type, right_type, result_type),
                        fail_message="Division in line {}".format(lineno))
    return result_type


def _infer_arithmetic(left_type, right_type, lineno):
    """Infer the type of an arithmetic operation, and add the corresponding axioms"""
    result_type = z3_types.new_z3_const("arithmetic_result")
    z3_types.solver.add(axioms.arithmetic(left_type, right_type, result_type),
                        fail_message="Arithmetic operation in line {}".format(lineno))
    return result_type


def _infer_bitwise(left_type, right_type, lineno):
    """Infer the type of a bitwise operation, and add the corresponding axioms"""
    result_type = z3_types.new_z3_const("bitwise_result")
    z3_types.solver.add(axioms.bitwise(left_type, right_type, result_type),
                        fail_message="Bitwise operation in line {}".format(lineno))
    return result_type


def binary_operation_type(left_type, op, right_type, lineno):
    """Infer the type of a binary operation result"""
    if isinstance(op, ast.Add):
        inference_func = _infer_add
    elif isinstance(op, ast.Mult):
        inference_func = _infer_mult
    elif isinstance(op, ast.Div):
        inference_func = _infer_div
    elif isinstance(op, (ast.BitOr, ast.BitXor, ast.BitAnd)):
        inference_func = _infer_bitwise
    else:
        inference_func = _infer_arithmetic

    return inference_func(left_type, right_type, lineno)


def infer_binary_operation(node, context):
    """Infer the type of binary operations

    Handled cases:
        - Sequence multiplication, ex: [1,2,3] * 2 --> [1,2,3,1,2,3]
        - Sequence concatenation, ex: [1,2,3] + [4,5,6] --> [1,2,3,4,5,6]
        - Arithmetic and bitwise operations, ex: (1 + 2) * 7 & (2 | -123) / 3
    """
    left_type = infer(node.left, context)
    right_type = infer(node.right, context)

    return binary_operation_type(left_type, node.op, right_type, node.lineno)


def infer_unary_operation(node, context):
    """Infer the type for unary operations

    Examples: -5, not 1, ~2
    """
    if isinstance(node.op, ast.Not):  # (not expr) always gives bool type
        return z3_types.Bool

    unary_type = infer(node.operand, context)

    if isinstance(node.op, ast.Invert):
        z3_types.solver.add(axioms.unary_invert(unary_type),
                            fail_message="Invert operation in line {}".format(node.lineno))
        return z3_types.Int
    else:
        result_type = z3_types.new_z3_const("unary_result")
        z3_types.solver.add(axioms.unary_other(unary_type, result_type),
                            fail_message="Unary operation in line {}".format(node.lineno))
        return result_type


def infer_if_expression(node, context):
    """Infer expressions like: {(a) if (test) else (b)}.

    Return a union type of both (a) and (b) types.
    """
    a_type = infer(node.body, context)
    b_type = infer(node.orelse, context)

    result_type = z3_types.new_z3_const("if_expr")
    z3_types.solver.add(axioms.if_expr(a_type, b_type, result_type),
                        fail_message="If expression in line {}".format(node.lineno))
    return result_type


def infer_subscript(node, context):
    """Infer expressions like: x[1], x["a"], x[1:2], x[1:].
    Where x	may be: a list, dict, tuple, str

    Attributes:
        node: the subscript node to be inferred
    """

    indexed_type = infer(node.value, context)

    if isinstance(node.slice, ast.Index):
        index_type = infer(node.slice.value, context)
        result_type = z3_types.new_z3_const("index")
        z3_types.solver.add(axioms.index(indexed_type, index_type, result_type),
                            fail_message="Indexing in line {}".format(node.lineno))
        return result_type
    else:  # Slicing
        # Some slicing may contain 'None' bounds, ex: a[1:], a[::]. Make Int the default type.
        lower_type = upper_type = step_type = z3_types.Int
        if node.slice.lower:
            lower_type = infer(node.slice.lower, context)
        if node.slice.upper:
            upper_type = infer(node.slice.upper, context)
        if node.slice.step:
            step_type = infer(node.slice.step, context)

        result_type = z3_types.new_z3_const("slice")

        z3_types.solver.add(axioms.slice(lower_type, upper_type, step_type, indexed_type, result_type),
                            fail_message="Slicing in line {}".format(node.lineno))
        return result_type


def infer_compare(node, context):
    # TODO: verify that types in comparison are comparable
    infer(node.left, context)
    for comparator in node.comparators:
        infer(comparator, context)

    return z3_types.Bool


def infer_name(node, context):
    """Infer the type of a variable

    Attributes:
        node: the variable node whose type is to be inferred
        context: The context to look in for the variable type
    """
    return context.get_type(node.id)


def infer_generators(generators, local_context, lineno):
    for gen in generators:
        iter_type = infer(gen.iter, local_context)
        target_type = z3_types.new_z3_const("generator_target")
        z3_types.solver.add(axioms.generator(iter_type, target_type),
                            fail_message="Generator in line {}".format(lineno))

        if not isinstance(gen.target, ast.Name):
            if not isinstance(gen.target, (ast.Tuple, ast.List)):
                raise TypeError("The iteration target should be only a variable name.")
            else:
                raise NotImplementedError("The inference doesn't support lists or tuples as iteration targets yet.")
        local_context.set_type(gen.target.id, target_type)


def infer_sequence_comprehension(node, sequence_type, context):
    """Infer the type of a list comprehension

    Attributes:
        node: the comprehension AST node to be inferred
        sequence_type: Either TList or TSet
        context: The current context level

    Examples:
        - [c * 2 for c in [1,2,3]] --> [2,4,6]
        - [c for b in [[1,2],[3,4]] for c in b] --> [1,2,3,4]
        - [(c + 1, c * 2) for c in [1,2,3]] --> [(2,2),(3,4),(4,6)]

    Limitation:
        The iterable should always be a list or a set (not a tuple or a dict)
        The iteration target should be always a variable name.
    """
    local_context = Context(parent_context=context)
    infer_generators(node.generators, local_context, node.lineno)
    return sequence_type(infer(node.elt, local_context))


def infer_dict_comprehension(node, context):
    """Infer the type of a dictionary comprehension

    Attributes:
        node: the dict comprehension AST node to be inferred
        context: The current context level

    Examples:
        - {a:(2 * a) for a in [1,2,3]} --> {1:2, 2:4, 3:6}
        - {a:len(a) for a in ["a","ab","abc"]}--> {"a":1, "ab":2, "abc":3}

    Limitation:
        The iterable should always be a list or a set (not a tuple or a dict)
        The iteration target should be always a variable name.
    """
    local_context = Context(parent_context=context)
    infer_generators(node.generators, local_context, node.lineno)
    key_type = infer(node.key, local_context)
    val_type = infer(node.value, local_context)
    return z3_types.Dict(key_type, val_type)


def _get_args_types(args, context):
    """Return inferred types for function call arguments"""
    # TODO kwargs

    args_types = ()
    for arg in args:
        args_types = args_types + (infer(arg, context),)
    return args_types


def infer_func_call(node, context):
    """Infer the type of a function call, and unify the call types with the function parameters"""
    called = infer(node.func, context)
    args_types = _get_args_types(node.args, context)

    result_type = z3_types.new_z3_const("call")

    # TODO covariant and invariant subtyping

    z3_types.solver.add(axioms.call(called, args_types, result_type),
                        fail_message="Call in line {}".format(node.lineno))

    return result_type


def infer_attribute(node, context):
    instance = infer(node.value, context)
    result_type = z3_types.new_z3_const("attribute")
    z3_types.solver.add(axioms.attribute(instance, node.attr, result_type),
                        fail_message="Attribute access in line {}".format(node.lineno))
    return result_type


def infer(node, context):
    """Infer the type of a given AST node"""
    if isinstance(node, ast.Num):
        return infer_numeric(node)
    elif isinstance(node, ast.Str):
        return z3_types.String
    elif (sys.version_info[0] >= 3 and sys.version_info[1] >= 6 and
            (isinstance(node, ast.FormattedValue) or isinstance(node, ast.JoinedStr))):
        # Formatted strings were introduced in Python 3.6
        return z3_types.String
    elif isinstance(node, ast.Bytes):
        return z3_types.Bytes
    elif isinstance(node, ast.List):
        return infer_list(node, context)
    elif isinstance(node, ast.Dict):
        return infer_dict(node, context)
    elif isinstance(node, ast.Tuple):
        return infer_tuple(node, context)
    elif isinstance(node, ast.NameConstant):
        return infer_name_constant(node)
    elif isinstance(node, ast.Set):
        return infer_set(node, context)
    elif isinstance(node, ast.BinOp):
        return infer_binary_operation(node, context)
    elif isinstance(node, ast.UnaryOp):
        return infer_unary_operation(node, context)
    elif isinstance(node, ast.IfExp):
        return infer_if_expression(node, context)
    elif isinstance(node, ast.Subscript):
        return infer_subscript(node, context)
    elif sys.version_info[0] >= 3 and sys.version_info[1] >= 5 and isinstance(node, ast.Await):
        # Await and Async were introduced in Python 3.5
        return infer(node.value, context)
    elif isinstance(node, ast.Yield):
        return infer(node.value, context)
    elif isinstance(node, ast.Compare):
        return infer_compare(node, context)
    elif isinstance(node, ast.Name):
        return infer_name(node, context)
    elif isinstance(node, ast.ListComp):
        return infer_sequence_comprehension(node, z3_types.List, context)
    elif isinstance(node, ast.SetComp):
        return infer_sequence_comprehension(node, z3_types.Set, context)
    elif isinstance(node, ast.DictComp):
        return infer_dict_comprehension(node, context)
    elif isinstance(node, ast.Call):
        return infer_func_call(node, context)
    elif isinstance(node, ast.Attribute):
        return infer_attribute(node, context)
    raise NotImplementedError("Inference for expression {} is not implemented yet.".format(type(node).__name__))
