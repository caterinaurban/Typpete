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

TODO:
    - Lambda(arguments args, expr body)
    - GeneratorExp(expr elt, comprehension* generators)
    - YieldFrom(expr value)
    - Call(expr func, expr* args, keyword* keywords)
    - Attribute(expr value, identifier attr, expr_co0ontext ctx)
    - Starred(expr value, expr_context ctx)
"""

import ast
import frontend.predicates as pred
import sys

from frontend.i_types import *


def _filter_types(types, types_filter, *preds):
    return {t for t in types if (pred.has_supertype(types_filter, t) or pred.satisfies_predicates(t, *preds))}


def narrow_types(original, types_filter, *preds):
    if not isinstance(original, UnionTypes):
        if not (pred.has_supertype(types_filter, original) or pred.satisfies_predicates(original, *preds)):
            raise TypeError("Cannot narrow types. The original type {} doesn't exist in the types filter {}."
                            .format(original, types_filter))
        else:
            return original
    else:
        intersection = _filter_types(original.types, types_filter, *preds)
        if len(intersection) == 0:
            TypeError("Cannot narrow types. The original types set {} doesn't intersect with the types filter {}."
                      .format(original, types_filter))
        elif len(intersection) == 1:
            return list(intersection)[0]
        else:
            return UnionTypes(intersection)


def infer_numeric(node):
    """Infer the type of a numeric node"""
    if type(node.n) == int:
        return TInt()
    if type(node.n) == float:
        return TFloat()
    if type(node.n) == complex:
        return TComplex()


def _get_elements_types(elts, context):
    if len(elts) == 0:
        return TNone()
    types = UnionTypes()
    for i in range(0, len(elts)):
        cur_type = infer(elts[i], context)
        types.union(cur_type)

    if len(types.types) == 1:
        return list(types.types)[0]
    return types


def infer_list(node, context):
    """Infer the type of a homogeneous list

    Returns: TList(Type t), where t is the type of the list elements
    """
    return TList(_get_elements_types(node.elts, context))


def infer_dict(node, context):
    """Infer the type of a dictionary with homogeneous key set and value set

    Returns: TDictionary(Type k_t, Type v_t), where:
            k_t is the type of dictionary keys
            v_t is the type of dictionary values
    """
    keys_type = _get_elements_types(node.keys, context)
    values_type = _get_elements_types(node.values, context)
    return TDictionary(keys_type, values_type)


def infer_tuple(node, context):
    """Infer the type of a tuple

    Returns: TTuple(Type[] t), where t is a list of the tuple's elements types
    """
    tuple_types = []
    for elem in node.elts:
        elem_type = infer(elem, context)
        tuple_types.append(elem_type)

    return TTuple(tuple_types)


def infer_name_constant(node):
    """Infer the type of name constants like: True, False, None"""
    if isinstance(node.value, bool):
        return TBool()
    elif node.value is None:
        return TNone()
    raise NotImplementedError("The inference for {} is not supported.".format(node.value))


def infer_set(node, context):
    """Infer the type of a homogeneous set

    Returns: TSet(Type t), where t is the type of the set elements
    """
    return TSet(_get_elements_types(node.elts, context))


def _get_stronger_numeric(num1, num2):
    return num1 if num1.strength > num2.strength else num2


def _infer_add(left_type, right_type):
    if isinstance(left_type, TNumber) and isinstance(right_type, TNumber):
        # arithmetic addition
        return _get_stronger_numeric(left_type, right_type)

    if isinstance(left_type, TSequence) and isinstance(right_type, TSequence):
        # sequence concatenation
        if isinstance(left_type, TTuple) and isinstance(right_type, TTuple):
            new_tuple_types = left_type.types + right_type.types
            return TTuple(new_tuple_types)
        if isinstance(left_type, TString) and isinstance(right_type, TString):
            return TString()
        if isinstance(left_type, TBytesString) and isinstance(right_type, TBytesString):
            return TBytesString()
        if isinstance(left_type, TList) and isinstance(right_type, TList):
            list_types = UnionTypes()
            list_types.union(left_type.type)
            list_types.union(right_type.type)
            return TList(list_types if len(list_types.types) > 1 else list(list_types.types)[0])

    raise TypeError("Cannot perform operation + on two types {} and {}".format(left_type, right_type))


def _infer_mult(left_type, right_type):
    if isinstance(left_type, TNumber) and isinstance(right_type, TNumber):
        return _get_stronger_numeric(left_type, right_type)
    # TODO handle tuple multiplication
    if isinstance(left_type, TSequence) and right_type.is_subtype(TInt()):
        return left_type
    if isinstance(right_type, TSequence) and left_type.is_subtype(TInt()):
        return right_type

    raise TypeError("Cannot perform operation * on two types {} and {}".format(left_type, right_type))


def _infer_div(left_type, right_type):
    if isinstance(left_type, TNumber) and isinstance(right_type, TNumber):
        return TFloat()
    raise TypeError("Cannot perform operation / on two types {} and {}".format(left_type, right_type))


def _infer_arithmetic(left_type, right_type):
    if isinstance(left_type, TNumber) and isinstance(right_type, TNumber):
        return _get_stronger_numeric(left_type, right_type)
    raise TypeError("Cannot perform arithmetic operation on two types {} and {}".format(left_type, right_type))


def _infer_bitwise(left_type, right_type):
    if left_type.is_subtype(TInt()) and right_type.is_subtype(TInt()):
        return _get_stronger_numeric(left_type, right_type)
    raise TypeError("Cannot perform bitwise operation on two types {} and {}".format(left_type, right_type))


def binary_operation_type(left_type, op, right_type):
    left_type = UnionTypes({left_type})
    right_type = UnionTypes({right_type})

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

    result_type = UnionTypes()
    for l_t in left_type.types:
        for r_t in right_type.types:
            result_type.union(inference_func(l_t, r_t))

    if len(result_type.types) == 0:
        raise TypeError("Cannot perform operation ({}) on two types: {} and {}".format(type(op).__name__,
                                                                                       left_type, right_type))
    elif len(result_type.types) == 1:
        return list(result_type.types)[0]
    return result_type


def infer_binary_operation(node, context):
    """Infer the type of binary operations

    Handled cases:
        - Sequence multiplication, ex: [1,2,3] * 2 --> [1,2,3,1,2,3]
        - Sequence concatenation, ex: [1,2,3] + [4,5,6] --> [1,2,3,4,5,6]
        - Arithmetic and bitwise operations, ex: (1 + 2) * 7 & (2 | -123) / 3
    """
    left_type = infer(node.left, context)
    right_type = infer(node.right, context)

    return binary_operation_type(left_type, node.op, right_type)


def infer_unary_operation(node, context):
    """Infer the type for unary operations

    Examples: -5, not 1, ~2
    """
    if isinstance(node.op, ast.Not):  # (not expr) always gives bool type
        return TBool()

    unary_type = UnionTypes({infer(node.operand, context)})
    result_type = UnionTypes()
    for t in unary_type.types:
        if isinstance(node.op, ast.Invert):
            if t.is_subtype(TInt()):
                result_type.union(TInt())
            else:
                raise TypeError("Cannot perform ~ operation on type {}.".format(t))
        else:
            if isinstance(t, TNumber):
                if isinstance(t, TBool):
                    result_type.union(TInt())
                else:
                    result_type.union(t)
            else:
                raise TypeError("Cannot perform unary operation on type {}.".format(t))
    if len(result_type.types) == 1:
        return list(result_type.types)[0]
    return result_type


def infer_if_expression(node, context):
    """Infer expressions like: {(a) if (test) else (b)}.

    Return a union type of both (a) and (b) types.
    """
    a_type = infer(node.body, context)
    b_type = infer(node.orelse, context)

    result_type = UnionTypes({a_type, b_type})
    if len(result_type.types) == 1:
        return list(result_type.types)[0]
    else:
        return result_type


def _infer_index_subscript(indexed_type, index_type):
    if pred.is_sequence(indexed_type):
        if not index_type.is_subtype(TInt()):
            raise KeyError("Cannot index a sequence with an index of type {}.".format(index_type))

    if isinstance(indexed_type, TString):
        return TString()
    if isinstance(indexed_type, TList):
        return indexed_type.type
    if isinstance(indexed_type, TTuple):
        tuple_types = UnionTypes(indexed_type.types)
        return tuple_types
    if isinstance(indexed_type, TDictionary):
        # Dictionaries may have union key set
        keys_types = UnionTypes(indexed_type.key_type)
        for k in keys_types.types:
            if index_type.is_subtype(k):
                return indexed_type.value_type
        raise KeyError("Cannot index a dict of type {} with an index of type {}.".format(indexed_type, index_type))
    raise TypeError("Cannot index {}.".format(indexed_type))


def _infer_slice_subscript(sliced_type):
    if not pred.is_sequence(sliced_type):
        raise TypeError("Cannot slice a non sequence.")
    if isinstance(sliced_type, TTuple):
        return sliced_type.get_possible_tuple_slicings()
    if pred.is_sequence(sliced_type):
        return sliced_type
    raise TypeError("Cannot slice a non sequence.")


def _all_int(union):
    for t in union.types:
        if not t.is_subtype(TInt()):
            return False
    return True


def infer_subscript(node, context):
    """Infer expressions like: x[1], x["a"], x[1:2], x[1:].
    Where x	may be: a list, dict, tuple, str

    Attributes:
        node: the subscript node to be inferred
    """

    indexed_types = UnionTypes(infer(node.value, context))

    subscript_type = UnionTypes()
    if isinstance(node.slice, ast.Index):
        index_types = UnionTypes(infer(node.slice.value, context))
        for index_t in index_types.types:
            for indexed_t in indexed_types.types:
                subscript_type.union(_infer_index_subscript(indexed_t, index_t))
    else:
        if node.slice.lower:
            lower_type = UnionTypes(infer(node.slice.lower, context))
            if not _all_int(lower_type):
                raise KeyError("Slicing lower bound should be integer.")
        if node.slice.upper:
            upper_type = UnionTypes(infer(node.slice.upper, context))
            if not _all_int(upper_type):
                raise KeyError("Slicing upper bound should be integer.")
        if node.slice.step:
            step_type = UnionTypes(infer(node.slice.step, context))
            if not _all_int(step_type):
                raise KeyError("Slicing step should be integer.")

        for indexed_t in indexed_types.types:
            subscript_type.union(indexed_t)

    if len(subscript_type.types) == 1:
        return list(subscript_type.types)[0]
    return subscript_type


def infer_compare(node):
    # TODO: verify that types in comparison are comparable
    return TBool()


def infer_name(node, context):
    """Infer the type of a variable

    Attributes:
        node: the variable node whose type is to be inferred
        context: The context to look in for the variable type
    """
    return context.get_type(node.id)


def infer_generators(generators, local_context):
    for gen in generators:
        iter_type = UnionTypes(infer(gen.iter, local_context))
        if not (pred.all_instance(iter_type, (TList, TSet, TDictionary))):
            raise TypeError("The iterable should be only a list, a set or a dict. Found {}.", iter_type)

        target_type = UnionTypes()
        for i_t in iter_type.types:
            if isinstance(i_t, (TList, TSet)):
                target_type.union(i_t.type)
            elif isinstance(i_t, TDictionary):
                target_type.union(i_t.key_type)

        if len(target_type.types) == 1:
            target_type = list(target_type.types)[0]

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
    infer_generators(node.generators, local_context)
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
    infer_generators(node.generators, local_context)
    key_type = infer(node.key, local_context)
    val_type = infer(node.value, local_context)
    return TDictionary(key_type, val_type)


def infer(node, context):
    """Infer the type of a given AST node"""
    if isinstance(node, ast.Num):
        return infer_numeric(node)
    elif isinstance(node, ast.Str):
        return TString()
    elif (sys.version_info[0] >= 3 and sys.version_info[1] >= 6 and
              (isinstance(node, ast.FormattedValue) or isinstance(node, ast.JoinedStr))):
        # Formatted strings were introduced in Python 3.6
        return TString()
    elif isinstance(node, ast.Bytes):
        return TBytesString()
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
        return infer_compare(node)
    elif isinstance(node, ast.Name):
        return infer_name(node, context)
    elif isinstance(node, ast.ListComp):
        return infer_sequence_comprehension(node, TList, context)
    elif isinstance(node, ast.SetComp):
        return infer_sequence_comprehension(node, TSet, context)
    elif isinstance(node, ast.DictComp):
        return infer_dict_comprehension(node, context)
    raise NotImplementedError("Inference for expression {} is not implemented yet.".format(type(node).__name__))
