"""Inferrer for python expressions.

Infers the types for the following expressions:
     - BinOp(expr left, operator op, expr right)
     - *UnaryOp(unaryop op, expr operand)
     - *Lambda(arguments args, expr body)
     - *IfExp(expr test, expr body, expr orelse)
     - Dict(expr* keys, expr* values)
     - Set(expr* elts)
     - ListComp(expr elt, comprehension* generators)
     - *SetComp(expr elt, comprehension* generators)
     - *DictComp(expr key, expr value, comprehension* generators)
     - *GeneratorExp(expr elt, comprehension* generators)
     - *Await(expr value)
     - *Yield(expr? value)
     - *YieldFrom(expr value)
     - *Compare(expr left, cmpop* ops, expr* comparators)
     - *Call(expr func, expr* args, keyword* keywords)
     - Num(object n) -- a number as a PyObject.
     - Str(string s) -- need to specify raw, unicode, etc?
     - *FormattedValue(expr value, int? conversion, expr? format_spec)
     - *JoinedStr(expr* values)
     - *Bytes(bytes s)
     - NameConstant(singleton value)
     - *Ellipsis
     - *Constant(constant value)
     - *Attribute(expr value, identifier attr, expr_context ctx)
     - *Subscript(expr value, slice slice, expr_context ctx)
     - *Starred(expr value, expr_context ctx)
     - *Name(identifier id, expr_context ctx)
     - List(expr* elts, expr_context ctx)
     - Tuple(expr* elts, expr_context ctx)

     *: Not implemented yet
"""

import types, ast
from abc import ABCMeta, abstractmethod
from exceptions import HomogeneousTypesConflict

def infer_numeric(node):
    if type(node.n) == int:
        return types.TInt()
    if type(node.n) == float:
        return types.TFloat()

def infer_list(node):
    if len(node.elts) == 0:
        return types.TList(types.TNone())
    list_type = infer(node.elts[0])
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i])
        if list_type.is_subtype(cur_type): # get the most generic type
            list_type = cur_type
        elif not cur_type.is_subtype(list_type): # make sure the list is homogeneous
            raise HomogeneousTypesConflict(list_type, cur_type)
    return types.TList(list_type)

def infer_dict(node):
    if len(node.keys) == 0:
        return types.TDictionary(types.TNone(), types.TNone())
    keys = node.keys
    values = node.values
    keys_type = infer(keys[0])
    values_type = infer(values[0])

    for i in range(1, len(keys)):
        cur_key_type = infer(keys[i])
        cur_value_type = infer(values[i])

        if keys_type.is_subtype(cur_key_type): # get the most generic keys type
            keys_type = cur_key_type
        elif not cur_key_type.is_subtype(keys_type): # make sure the dict key set is homogeneous
            raise HomogeneousTypesConflict(keys_type, cur_key_type)

        if values_type.is_subtype(cur_value_type): # get the most generic values type
            values_type = cur_value_type
        elif not cur_value_type.is_subtype(values_type): # make sure the dict value set is homogeneous
            raise HomogeneousTypesConflict(values_type, cur_value_type)
    return types.TDictionary(keys_type, values_type)

def infer_tuple(node):
    tuple_types = []
    for elem in node.elts:
        elem_type = infer(elem)
        tuple_types.append(elem_type)

    return types.TTuple(tuple_types)

def infer_name_constant(node):
    if node.value == True or node.value == False:
        return types.TBool()
    elif node.value == None:
        return types.TNone()

def infer_set(node):
    if len(node.elts) == 0:
        return types.TSet(types.TNone)
    set_type = infer(node.elts[0])
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i])
        if set_type.is_subtype(cur_type): # get the most generic type
            set_type = cur_type
        elif not cur_type.is_subtype(set_type): # make sure the set is homogeneous
            raise HomogeneousTypesConflict(set_type, cur_type)
    return types.TSet(set_type)

def infer_binary_operation(node):
    left_type = infer(node.left)
    right_type = infer(node.right)
    if isinstance(node.op, ast.Div): # Check if it is a float division operation
        if left_type.is_subtype(types.TFloat()) and right_type.is_subtype(types.TFloat()):
            return types.TFloat()
    if left_type.is_subtype(right_type):
        return right_type
    elif right_type.is_subtype(left_type):
        return left_type
    raise TypeError("The left and right types should be subtypes of each other.")

def infer(node):
    if isinstance(node, ast.Num):
        return infer_numeric(node)
    elif isinstance(node, ast.Str):
        return types.TString()
    elif isinstance(node, ast.List):
        return infer_list(node)
    elif isinstance(node, ast.Dict):
        return infer_dict(node)
    elif isinstance(node, ast.Tuple):
        return infer_tuple(node)
    elif isinstance(node, ast.NameConstant):
        return infer_name_constant(node)
    elif isinstance(node, ast.Set):
        return infer_set(node)
    elif isinstance(node, ast.BinOp):
        return infer_binary_operation(node)
    return types.TNone()
