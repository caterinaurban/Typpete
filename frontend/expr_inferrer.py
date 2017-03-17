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
	 - Subscript(expr value, slice slice, expr_context ctx)
	 - Await(expr value) --> Python 3.5+
	 - Yield(expr? value)
     - Compare(expr left, cmpop* ops, expr* comparators)
     - Name(identifier id, expr_context ctx)
     - FormattedValue(expr value, int? conversion, expr? format_spec) --> Python 3.6+
     - JoinedStr(expr* values) --> Python 3.6+
     - ListComp(expr elt, comprehension* generators)

     TODO:
     - Lambda(arguments args, expr body)
     - SetComp(expr elt, comprehension* generators)
     - DictComp(expr key, expr value, comprehension* generators)
     - GeneratorExp(expr elt, comprehension* generators)
     - YieldFrom(expr value)
     - Call(expr func, expr* args, keyword* keywords)
     - Attribute(expr value, identifier attr, expr_co0ontext ctx)
     - Starred(expr value, expr_context ctx)

     TODO:
     - Infer (or narrow) types based on context. For example, in the following expression:
        (x + 2) * 3
        if the type of x is still not inferred (or inferred to be a union type), we can infer (narrow) that x
        is a numeric value (TBool, TInt or TFloat)
        Affected inference functions:
            - infer_binary_operation
            - infer_unary_operation
            - infer_subscript
            - infer_compare
"""

import ast, sys
from i_types import *
from context import Context
from abc import ABCMeta, abstractmethod
from exceptions import HomogeneousTypesConflict

def infer_numeric(node):
    """Infer the type of a numeric node"""
    if type(node.n) == int:
        return TInt()
    if type(node.n) == float:
        return TFloat()

def infer_list(node, context):
    """Infer the type of a homogeneous list

    Returns: TList(Type t), where t is the type of the list elements
    """
    if len(node.elts) == 0:
        return TList(TNone())
    list_type = infer(node.elts[0], context)
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i], context)
        if list_type.is_subtype(cur_type): # get the most generic type
            list_type = cur_type
        elif not cur_type.is_subtype(list_type): # make sure the list is homogeneous
            raise HomogeneousTypesConflict(list_type.get_name(), cur_type.get_name())
    return TList(list_type)

def infer_dict(node, context):
    """Infer the type of a dictionary with homogeneous key set and value set

    Returns: TDictionary(Type k_t, Type v_t), where:
            k_t is the type of dictionary keys
            v_t is the type of dictionary values
    """
    if len(node.keys) == 0:
        return TDictionary(TNone(), TNone())
    keys = node.keys
    values = node.values
    keys_type = infer(keys[0], context)
    values_type = infer(values[0], context)

    for i in range(1, len(keys)):
        cur_key_type = infer(keys[i], context)
        cur_value_type = infer(values[i], context)

        if keys_type.is_subtype(cur_key_type): # get the most generic keys type
            keys_type = cur_key_type
        elif not cur_key_type.is_subtype(keys_type): # make sure the dict key set is homogeneous
            raise HomogeneousTypesConflict(keys_type.get_name(), cur_key_type.get_name())

        if values_type.is_subtype(cur_value_type): # get the most generic values type
            values_type = cur_value_type
        elif not cur_value_type.is_subtype(values_type): # make sure the dict value set is homogeneous
            raise HomogeneousTypesConflict(values_type.get_name(), cur_value_type.get_name())
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
    if node.value == True or node.value == False:
        return TBool()
    elif node.value == None:
        return TNone()

def infer_set(node, context):
    """Infer the type of a homogeneous set

    Returns: TSet(Type t), where t is the type of the set elements
    """
    if len(node.elts) == 0:
        return TSet(TNone)
    set_type = infer(node.elts[0], context)
    for i in range(1, len(node.elts)):
        cur_type = infer(node.elts[i], context)
        if set_type.is_subtype(cur_type): # get the most generic type
            set_type = cur_type
        elif not cur_type.is_subtype(set_type): # make sure the set is homogeneous
            raise HomogeneousTypesConflict(set_type.get_name(), cur_type.get_name())
    return TSet(set_type)

def is_numeric(t):
	return t.is_subtype(TFloat())

def infer_binary_operation(node, context):
    """Infer the type of binary operations

    Handled cases:
        - Sequence multiplication, ex: [1,2,3] * 2 --> [1,2,3,1,2,3]
        - Sequence concatenation, ex: [1,2,3] + [4,5,6] --> [1,2,3,4,5,6]
        - Arithmatic and bitwise operations, ex: (1 + 2) * 7 & (2 | -123) / 3
    """
    left_type = infer(node.left, context)
    right_type = infer(node.right, context)

    if isinstance(node.op, ast.Mult):
        # Handle sequence multiplication. Ex.:
        # [1,2,3] * 2 --> [1,2,3,1,2,3]
        # 2 * "abc" -- > "abcabc"
        if left_type.is_subtype(TInt()) and is_sequence(right_type):
            return right_type
        elif right_type.is_subtype(TInt()) and is_sequence(left_type):
            return left_type

    if isinstance(node.op, ast.Add): # Check if it is a concatenation operation between sequences
        if isinstance(left_type, TTuple) and isinstance(right_type, TTuple):
            # Handle tuples concatenation:
            # (1, 2.0, "string") + (True, X()) --> (1, 2.0, "string", True, X())
            # The result type is the concatenation of both tuples' types
            new_tuple_types = left_type.types + right_type.types
            return TTuple(new_tuple_types)

        if is_sequence(left_type) and is_sequence(right_type):
            if left_type.is_subtype(right_type):
                return right_type
            elif right_type.is_subtype(left_type):
                return left_type

    if isinstance(node.op, ast.Div): # Check if it is a float division operation
        if left_type.is_subtype(TFloat()) and right_type.is_subtype(TFloat()):
            return TFloat()

    if is_numeric(left_type) and is_numeric(right_type): # Normal arithmatic or bitwise operation
        # TODO: Prevent floats from doing bitwise operations
        if left_type.is_subtype(right_type):
            return right_type
        elif right_type.is_subtype(left_type):
            return left_type

    raise TypeError("Cannot perform operation ({}) on two types: {} and {}".format(type(node.op).__name__, left_type.get_name(), right_type.get_name()))

def infer_unary_operation(node, context):
    """Infer the type for unary operations

    Examples: -5, not 1, ~2
    """
    if isinstance(node.op, ast.Not): # (not expr) always gives bool type
        return TBool()
    # TODO: prevent floats from doing the unary operator '~'
    return infer(node.operand, context)

def infer_if_expression(node, context):
    """Infer expressions like: {(a) if (test) else (b)}.

    Return a union type of both (a) and (b) types.
    """
    a_type = infer(node.body, context)
    b_type = infer(node.orelse, context)

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
	"""

	indexed_type = infer(node.value, context)
	if not can_be_indexed(indexed_type):
		raise TypeError("Cannot perform subscripting on {}.".format(indexed_type.get_name()))

	if isinstance(node.slice, ast.Index):
        # Indexing
		index_type = infer(node.slice.value, context)
		if is_sequence(indexed_type):
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
        # Slicing
		if not is_sequence(indexed_type):
			raise TypeError("Cannot slice {}.".format(indexed_type.get_name()))
		lower_type = infer(node.slice.lower, context)
		upper_type = infer(node.slice.upper, context)
		step_type = infer(node.slice.step, context)

		if not (lower_type.is_subtype(TInt()) and upper_type.is_subtype(TInt()) and step_type.is_subtype(TInt())):
			raise KeyError("Slicing bounds and step should be integers.")
		if isinstance(indexed_type, TTuple):
			return indexed_type.get_possible_tuple_slicings()
		else:
			return indexed_type

def infer_compare(node):
    return TBool()

def infer_name(node, context):
    """Infer the type of a variable

    Attributes:
        node: the variable node whose type is to be inferred
        context: The context to look in for the variable type
    """
    return context.get_type(node.id)

def infer_list_comprehension(node, context):
    """Infer the type of a list comprehension

    Examples:
        - [c * 2 for c in [1,2,3]] --> [2,4,6]
        - [c for b in [[1,2],[3,4]] for c in b] --> [1,2,3,4]
        - [(c + 1, c * 2) for c in [1,2,3]] --> [(2,2),(3,4),(4,6)]

    Limitation:
        The iterable should always be a list or a set (not a tuple)
        The iteration target should be always a variable name.
    """
    local_context = Context(parent_context=context)
    for gen in node.generators:
        iter_type = infer(gen.iter, local_context)
        if not (isinstance(iter_type, TList) or isinstance(iter_type, TSet)):
            raise TypeError("The iterable should be only a list or a set. Found {}.", iter_type.get_name())
        target_type = iter_type.type # Get the type of list/set elements

        if not isinstance(gen.target, ast.Name):
            raise TypeError("The iteration target should be only a variable name.")
        local_context.set_type(gen.target.id, target_type)

    return TList(infer(node.elt, local_context))


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
        return infer_list_comprehension(node, context)
    return TNone()

global_context = Context()
