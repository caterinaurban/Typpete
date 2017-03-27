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
     - SetComp(expr elt, comprehension* generators)
     - DictComp(expr key, expr value, comprehension* generators)

     TODO:
     - Lambda(arguments args, expr body)
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
            - infer_subscript
            - infer_compare
"""

import ast, sys, predicates as pred
from i_types import *
from context import Context
from abc import ABCMeta, abstractmethod
from exceptions import HomogeneousTypesConflict

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

def _get_common_supertype(elts, context):
    if len(elts) == 0:
        return TNone()
    supertype = infer(elts[0], context)
    for i in range(1, len(elts)):
        cur_type = infer(elts[i], context)
        if supertype.is_subtype(cur_type): # get the most generic type
            supertype = cur_type
        elif not cur_type.is_subtype(supertype): # make sure the list is homogeneous
            raise HomogeneousTypesConflict(supertype, cur_type)
    return supertype

def infer_list(node, context):
    """Infer the type of a homogeneous list

    Returns: TList(Type t), where t is the type of the list elements
    """
    return TList(_get_common_supertype(node.elts, context))

def infer_dict(node, context):
    """Infer the type of a dictionary with homogeneous key set and value set

    Returns: TDictionary(Type k_t, Type v_t), where:
            k_t is the type of dictionary keys
            v_t is the type of dictionary values
    """
    keys_type = _get_common_supertype(node.keys, context)
    values_type = _get_common_supertype(node.values, context)
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
    elif node.value is None:
        return TNone()
    raise NotImplementedError("The inference for {} is not supported.".format(node.value))

def infer_set(node, context):
    """Infer the type of a homogeneous set

    Returns: TSet(Type t), where t is the type of the set elements
    """
    return TSet(_get_common_supertype(node.elts, context))

def binary_operation_type(left_type, op, right_type):
    op_type = UnionTypes()
    if isinstance(op, ast.Mult):
        # Handle sequence multiplication. Ex.:
        # [1,2,3] * 2 --> [1,2,3,1,2,3]
        # 2 * "abc" -- > "abcabc"
        try:
            narrowed_left = narrow_types(left_type, UnionTypes({TInt()}), pred.is_sequence)
            narrowed_right = narrow_types(right_type, UnionTypes({TInt()}), pred.is_sequence)
            if pred.has_subtype(narrowed_left, TInt()) and pred.has_sequence(right_type):
                op_type.union(narrow_types(right_type, UnionTypes(), pred.is_sequence))
            elif pred.has_subtype(narrowed_right, TInt()) and pred.has_sequence(left_type):
                op_type.union(narrow_types(left_type, UnionTypes(), pred.is_sequence))
        except TypeError:
            pass

    if isinstance(op, ast.Add): # Check if it is a concatenation operation between sequences
        if pred.has_instance(left_type, TTuple) and pred.has_instance(right_type, TTuple):
            # Handle tuples concatenation:
            # (1, 2.0, "string") + (True, X()) --> (1, 2.0, "string", True, X())
            # The result type is the concatenation of both tuples' types
            left_tuples = UnionTypes()
            right_tuples = UnionTypes()
            left_tuples.union(narrow_types(left_type, UnionTypes(), pred.is_tuple))
            right_tuples.union(narrow_types(right_type, UnionTypes(), pred.is_tuple))

            for tup1 in left_tuples.types:
                for tup2 in right_tuples.types:
                    new_tuple_types = tup1.types + tup2.types
                    op_type.union(TTuple(new_tuple_types))


        elif pred.has_sequence(left_type) and pred.has_sequence(right_type):
            left_sequences = UnionTypes()
            right_sequences = UnionTypes()
            left_sequences.union(narrow_types(left_type, UnionTypes(), pred.is_sequence))
            right_sequences.union(narrow_types(right_type, UnionTypes(), pred.is_sequence))

            for seq1 in left_sequences.types:
                for seq2 in right_sequences.types:
                    if seq1.is_subtype(seq2):
                        op_type.union(seq2)
                    elif seq2.is_subtype(seq1):
                        op_type.union(seq1)

    if isinstance(op, ast.Div): # Check if it is a float division operation
        if pred.has_subtype(left_type, TFloat()) and pred.has_subtype(right_type, TFloat()):
            op_type.union(TFloat())

    if pred.has_subtype(left_type, TFloat()) and pred.has_subtype(right_type, TFloat()): # Normal arithmatic or bitwise operation
        # TODO: Prevent floats from doing bitwise operations
        left_numeric = UnionTypes()
        right_numeric = UnionTypes()
        left_numeric.union(narrow_types(left_type, UnionTypes({TFloat()})))
        right_numeric.union(narrow_types(right_type, UnionTypes({TFloat()})))
        for num1 in left_numeric.types:
            for num2 in right_numeric.types:
                if num1.is_subtype(num2):
                    op_type.union(num2)
                elif num2.is_subtype(num1):
                    op_type.union(num1)

    if len(op_type.types) == 0:
        raise TypeError("Cannot perform operation ({}) on two types: {} and {}".format(type(op).__name__, left_type, right_type))
    elif len(op_type.types) == 1:
        return list(op_type.types)[0]
    else:
        return op_type

def infer_binary_operation(node, context):
    """Infer the type of binary operations

    Handled cases:
        - Sequence multiplication, ex: [1,2,3] * 2 --> [1,2,3,1,2,3]
        - Sequence concatenation, ex: [1,2,3] + [4,5,6] --> [1,2,3,4,5,6]
        - Arithmatic and bitwise operations, ex: (1 + 2) * 7 & (2 | -123) / 3
    """
    left_type = infer(node.left, context)
    right_type = infer(node.right, context)

    return binary_operation_type(left_type, node.op, right_type)

def infer_unary_operation(node, context):
    """Infer the type for unary operations

    Examples: -5, not 1, ~2
    """
    if isinstance(node.op, ast.Not): # (not expr) always gives bool type
        return TBool()

    unary_type = infer(node.operand, context)

    try:
        unary_type = narrow_types(unary_type, UnionTypes({TInt() if isinstance(node.op, ast.Invert) else TFloat()}))
    except TypeError:
        raise TypeError("Cannot perform unary operation ({}) on type {}.".format(type(node.op).__name__, unary_type))
    return unary_type

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

def infer_subscript(node, context):
	"""Infer expressions like: x[1], x["a"], x[1:2], x[1:].
	Where x	may be: a list, dict, tuple, str

	Attributes:
		node: the subscript node to be inferred
	"""

	indexed_type = infer(node.value, context)
	if not pred.can_be_indexed(indexed_type):
		raise TypeError("Cannot perform subscripting on {}.".format(indexed_type))

	if isinstance(node.slice, ast.Index):
        # Indexing
		index_type = infer(node.slice.value, context)
		if pred.is_sequence(indexed_type):
			if not index_type.is_subtype(TInt()):
				raise KeyError("Cannot index a sequence with an index of type {}.".format(index_type))
			if isinstance(indexed_type, TString):
				return TString()
			elif isinstance(indexed_type, TList):
				return indexed_type.type
			elif isinstance(indexed_type, TTuple):
				return UnionTypes(indexed_type.types)
		elif isinstance(indexed_type, TDictionary):
			if not index_type.is_subtype(indexed_type.key_type):
				raise KeyError("Cannot index a dictionary of type {} with an index of type {}.".format(indexed_type, index_type))
			return indexed_type.value_type
	elif isinstance(node.slice, ast.Slice):
        # Slicing
		if not pred.is_sequence(indexed_type):
			raise TypeError("Cannot slice {}.".format(indexed_type))
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

def infer_generators(generators, local_context):
    for gen in generators:
        iter_type = infer(gen.iter, local_context)
        if not (isinstance(iter_type, TList) or isinstance(iter_type, TSet)):
            raise TypeError("The iterable should be only a list or a set. Found {}.", iter_type)
        target_type = iter_type.type # Get the type of list/set elements

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
    return TNone()
