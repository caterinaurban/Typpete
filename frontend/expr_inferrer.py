"""Inferrer for python expressions.

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

     TODO:
     - Lambda(arguments args, expr body)
     - ListComp(expr elt, comprehension* generators)
     - SetComp(expr elt, comprehension* generators)
     - DictComp(expr key, expr value, comprehension* generators)
     - GeneratorExp(expr elt, comprehension* generators)
     - Await(expr value)
     - Yield(expr? value)
     - YieldFrom(expr value)
     - Compare(expr left, cmpop* ops, expr* comparators)
     - Call(expr func, expr* args, keyword* keywords)
     - FormattedValue(expr value, int? conversion, expr? format_spec)
     - JoinedStr(expr* values)
     - Ellipsis
     - Constant(constant value)
     - Attribute(expr value, identifier attr, expr_context ctx)
     - Subscript(expr value, slice slice, expr_context ctx)
     - Starred(expr value, expr_context ctx)
     - Name(identifier id, expr_context ctx)
"""

import ast
from i_types import *
from abc import ABCMeta, abstractmethod
from exceptions import HomogeneousTypesConflict

def infer_numeric(node):
    if type(node.n) == int:
        return TInt()
    if type(node.n) == float:
        return TFloat()

def infer_list(node):
    if len(node.elts) == 0:
        return TList(TNone())
    list_type = infer(node.elts[0])
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i])
        if list_type.is_subtype(cur_type): # get the most generic type
            list_type = cur_type
        elif not cur_type.is_subtype(list_type): # make sure the list is homogeneous
            raise HomogeneousTypesConflict(list_type.get_name(), cur_type.get_name())
    return TList(list_type)

def infer_dict(node):
    if len(node.keys) == 0:
        return TDictionary(TNone(), TNone())
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
            raise HomogeneousTypesConflict(keys_type.get_name(), cur_key_type.get_name())

        if values_type.is_subtype(cur_value_type): # get the most generic values type
            values_type = cur_value_type
        elif not cur_value_type.is_subtype(values_type): # make sure the dict value set is homogeneous
            raise HomogeneousTypesConflict(values_type.get_name(), cur_value_type.get_name())
    return TDictionary(keys_type, values_type)

def infer_tuple(node):
    tuple_types = []
    for elem in node.elts:
        elem_type = infer(elem)
        tuple_types.append(elem_type)

    return TTuple(tuple_types)

def infer_name_constant(node):
    if node.value == True or node.value == False:
        return TBool()
    elif node.value == None:
        return TNone()

def infer_set(node):
    if len(node.elts) == 0:
        return TSet(TNone)
    set_type = infer(node.elts[0])
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i])
        if set_type.is_subtype(cur_type): # get the most generic type
            set_type = cur_type
        elif not cur_type.is_subtype(set_type): # make sure the set is homogeneous
            raise HomogeneousTypesConflict(set_type.get_name(), cur_type.get_name())
    return TSet(set_type)

def infer_binary_operation(node):
    left_type = infer(node.left)
    right_type = infer(node.right)
    if isinstance(node.op, ast.Div): # Check if it is a float division operation
        if left_type.is_subtype(TFloat()) and right_type.is_subtype(TFloat()):
            return TFloat()
    if left_type.is_subtype(right_type):
        return right_type
    elif right_type.is_subtype(left_type):
        return left_type
    if isinstance(node.op, ast.Mult):
        # Handle sequence multiplication. Ex.:
        # [1,2,3] * 2 --> [1,2,3,1,2,3]
        # 2 * "abc" -- > "abcabc"
        if left_type.is_subtype(TInt()):
            return right_type
        elif right_type.is_subtype(TInt()):
            return left_type

    raise TypeError("Cannot perform operation ({}) on two types: {} and {}".format(type(node.op).__name__, left_type.get_name(), right_type.get_name()))

def infer_unary_operation(node):
    if isinstance(node.op, ast.Not): # (not expr) always gives bool type
        return TBool()
    return infer(node.operand)

def infer_if_expression(node):
    """Infer expressions like: {(a) if (test) else (b)}.

    Return a union type of both (a) and (b) types.
    """
    a_type = infer(node.body)
    b_type = infer(node.orelse)

    if type(a_type) is type(b_type):
        return a_type

    return UnionTypes({a_type, b_type})

def is_sequence(t):
	return isinstance(t, (TList, TTuple, TString))

def can_be_indexed(t):
    return is_sequence(t) or isinstance(t, TDictionary)

def infer_subscript(node, context):
	"""Infer expressions like: x[1], x["a"], x[1:2], x[1:].
	Where x	may be: a list, dict, tuple, str

	Attributes:
		node: the subscript node to be inferred
		context: the context containing the mapping between already inferred variables and their types
	"""
	
	indexed_type = infer(node.value, context)
	if not can_be_indexed(indexed_type):
		raise TypeError("Cannot perform subscripting on {}.".format(indexed_type.get_name()))

	if isinstance(node.slice, ast.Index):
		index_type = infer(node.slice.value)
		if isinstance(indexed_type, (TList, TTuple, TString)):
			if not index_type.is_subtype(TInt()):
				raise KeyError("Cannot index a sequence with an index of type {}.".format(index_type.get_name()))
			if isinstance(indexed_type, TString):
				return TString()
			elif isinstance(indexed_type, TList):
				return indexed_type.type
			elif isinstance(indexed_type, TTuple):
				return UnionTypes(indexed_type.types)
		elif isinstance(indexed_type, TDictionary):
			if not index_type.is_subtype(indexed_type.key_type):
				raise KeyError("Cannot index a dictionary of type {} with an index of type {}.".format(indexed_type.get_name(), index_type.get_name()))
			return indexed_type.value_type
	elif isinstance(node.slice, ast.Slice):
		if not is_sequence(indexed_type):
			raise TypeError("Cannot slice {}.".format(indexed_type.get_name()))
		lower_type = infer(node.slice.lower)
		upper_type = infer(node.slice.upper)
		step_type = infer(node.slice.step)

		if not (lower_type.is_subtype(TInt()) and upper_type.is_subtype(TInt()) and step_type.is_subtype(TInt())):
			raise KeyError("Slicing bounds and step should be integers.")
		if isinstance(indexed_type, TTuple):
			return indexed_type.get_possible_tuple_slicings()
		else:
			return indexed_type

def infer(node, context=None):
    if isinstance(node, ast.Num):
        return infer_numeric(node)
    elif isinstance(node, ast.Str):
        return TString()
    elif isinstance(node, ast.Bytes):
        return TBytesString()
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
    elif isinstance(node, ast.UnaryOp):
        return infer_unary_operation(node)
    elif isinstance(node, ast.IfExp):
        return infer_if_expression(node)
    elif isinstance(node, ast.Subscript):
        return infer_subscript(node, context)
    return TNone()

