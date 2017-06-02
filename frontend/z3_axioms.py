from frontend.z3_types import And, Or, Implies, Exists, Not, Const


def add(left, right, result, types):
    """Constraints for the addition operation
    
    Cases:
        - Number_1 + Number_2 --> Stronger(Number_1, Number_2)
        - Sequence + Sequence --> Sequence
    
    Ex:
        - 1 + 2.0
        - [1, 2, 3] + [4]
        - "string" + "string2"
    
    """
    return [
        Or(
            And(types.subtype(left, types.num), types.subtype(right, types.num), types.subtype(result, types.num)),
            And(types.subtype(left, types.seq), left == right, left == result)
        ),

        Implies(And(types.subtype(left, types.num), types.stronger_num(left, right)), result == left),
        Implies(And(types.subtype(left, types.num), types.stronger_num(right, left)), result == right)
    ]


def mult(left, right, result, types):
    """Constraints for the multiplication operation
    
    Cases:
        - Number_1 * Number_2 --> Stronger(Number_1, Number_2)
        - Int * Sequence --> Sequence
        - Sequence * Int --> Sequence
        
    Ex:
        - 1 * 2.0
        - 3 * [1, 2]
        - b"string" * 4
    """
    return [
        Or(
            And(types.subtype(left, types.int), types.subtype(right, types.seq), result == right),
            And(types.subtype(left, types.seq), types.subtype(right, types.int), result == left),
            And(types.subtype(left, types.num), types.subtype(right, types.num), types.subtype(result, types.num))
        ),

        Implies(
            And(types.subtype(left, types.num), types.subtype(right, types.num), types.stronger_num(left, right)),
            result == left
        ),

        Implies(
            And(types.subtype(left, types.num), types.subtype(right, types.num), types.stronger_num(right, left)),
            result == right
        )
    ]


def div(left, right, result, types):
    """Constraints for the division operation

    Cases:
        - Number_1 / Number_2 --> Stronger(types.float, Stronger(Number_1, Number2))
        
    Ex:
        - True / 7
        - 3 / (1 + 2j)
    """
    return [
        And(types.subtype(left, types.num), types.subtype(right, types.num)),
        Implies(Or(left == types.complex, right == types.complex), result == types.complex),
        Implies(Not(Or(left == types.complex, right == types.complex)), result == types.float)
    ]


def arithmetic(left, right, result, types):
    """Constraints for arithmetic operation

    Cases:
        - Number_1 (op) Number_2 --> Stronger(Number_1, Number_2)
        
    Ex:
        - 2 ** 3.0
        - 3 - 4
    """
    return [
        And(types.subtype(left, types.num), types.subtype(right, types.num)),
        Implies(types.stronger_num(left, right), result == left),
        Implies(types.stronger_num(right, left), result == right)
    ]


def bitwise(left, right, result, types):
    """Constraints for arithmetic operation

    Cases:
        - (Number_1: Int/Bool) (op) (Number_2: Int/Bool) --> Stronger(Number_1, Number_2)
        
    Ex:
        - 1 & 2
        - True ^ False
    """
    return arithmetic(left, right, result, types) + [
        And(types.subtype(left, types.int), types.subtype(right, types.int))]


def unary_invert(unary, types):
    """Constraints for the invert unary operation
    
    Only subtypes for int are eligible for this operation (No floats)
    
    Ex:
    - ~231
    """
    return [
        types.subtype(unary, types.int)
    ]


def unary_other(unary, result, types):
    """Constraints for any unary operation except (~) and (not)
    
    Cases:
        - (op) Number --> Stronger(Int, Number)
        
    Ex:
        - -True
        - +2.0
    """
    return [
        types.subtype(unary, types.num),
        Implies(unary == types.bool, result == types.int),
        Implies(unary != types.bool, result == unary)
    ]


def if_expr(a, b, result, types):
    """Constraints for if expressions
    
    Cases:
        - (a) if (TEST) else (b) --> Super(a, b)
    """
    return [
        types.subtype(a, result),
        types.subtype(b, result)
    ]


def index(indexed, ind, result, types):
    """Constraints for index subscript
    
    Cases:
        - List[t] --> t
        - str --> str
        - bytes --> bytes
        - Dict{t1: t2} --> t2
        - Tuple(t1, t2, t3, ..., tn) --> Super(t1, t2, t3, ..., tn)
    """

    # Tuple indexing
    # Assert that 'indexed' can be a tuple of an arbitrary length, where the result is the super-type of its elements.
    t = []
    quantifiers_consts = [Const("tuples_q_{}".format(x), types.type_sort) for x in range(len(types.tuples) - 1)]
    for cur_len in range(1, len(types.tuples)):
        quants = quantifiers_consts[:cur_len]
        t.append(Exists(quants, And(
            indexed == types.tuples[cur_len](*quants),
            *[types.subtype(x, result) for x in quants]
        ), patterns=[types.tuples[cur_len](*quants)]))

    return [
        Or(
            [indexed == types.dict(ind, result),
             And(types.subtype(ind, types.int), indexed == types.list(result)),
             And(types.subtype(ind, types.int), indexed == types.string, result == types.string),
             And(types.subtype(ind, types.int), indexed == types.bytes, result == types.bytes)]
            + t
        )
    ]


def slicing(lower, upper, step, sliced, result, types):
    """Constraints for slicing subscript
    
    Cases:
        - Sequence --> Sequence
    """
    return [
        And(types.subtype(lower, types.int), types.subtype(upper, types.int), types.subtype(step, types.int),
            types.subtype(sliced, types.seq), result == sliced)
    ]


def generator(iterable, target, types):
    """Constraints for comprehension generators
    
    Ex:
        - [x for x in [1, 2]]
        - [x for x in {1, 2}]
        - [x for y in ["st", "st"] for x in y]
        - [x for x in {1: "a", 2: "b"}]
    """
    # TODO tuples
    x = Const("x", types.type_sort)
    return [
        Or(
            iterable == types.list(target),
            iterable == types.set(target),
            And(iterable == types.string, target == types.string),
            And(iterable == types.bytes, target == types.bytes),
            Exists(x, iterable == types.dict(target, x), patterns=[types.dict(target, x)])
        )
    ]


def assignment(target, value, types):
    """Constraints for variable assignment.
    
    The left hand side is either a super type or a numerically stronger type of the right hand side.
    """
    return [
        Implies(types.subtype(target, types.num),
                And(types.subtype(value, types.num), types.stronger_num(target, value))),
        Implies(Not(types.subtype(target, types.num)), types.subtype(value, target))
    ]


def multiple_assignment(target, value, position, types):
    """Constraints for multiple assignments
    
    :param target: The type of the assignment target (LHS)
    :param value: The type of the assignment value (RHS)
    :param position: The position of the target/value in the multiple assignment
    :param types: The types object containing z3 types
    
    Cases:
        - List: a, b = [1, 2]
        - types.set: a, b = 1, "string"
        
    Ex:
        - a, b = [1, 2]
        
        The above example calls this function twice:
            * first time: target := type(a), value := type(1), position := 0
            * second time: target := type(b), value := type(2), position := 1
    """

    # List multiple assignment
    lst = [value == types.list(target)]

    # types.set multiple assignment:
    # Assert with tuples of different lengths, maintaining the correct position of the target in the tuple.
    t = []
    quantifiers_consts = [Const("tuples_q_{}".format(x), types.type_sort) for x in range(len(types.tuples) - 2)]
    for cur_len in range(position + 1, len(types.tuples)):
        before_target = quantifiers_consts[:position]  # The tuple elements before the target
        after_target = quantifiers_consts[position:cur_len - 1]  # The tuple elements after the target
        quants = before_target + after_target  # The quantifiers constants for this tuple length
        params = before_target + [target] + after_target  # The parameters to instantiate the tuple

        if quants:
            t.append(Exists(quants, value == types.tuples[cur_len](*params), patterns=[types.tuples[cur_len](*params)]))
        else:
            t.append(value == types.tuples[cur_len](*params))

    return [Or(lst + t)]


def index_assignment(indexed, ind, value, types):
    """Constraints for index subscript assignment
    
    Cases:
        - Dict
        - List
        
    Ex:
        - a["string"] = 2.0
        - b[0] = foo()
    """
    return [
        Or(
            indexed == types.dict(ind, value),
            And(types.subtype(ind, types.int), indexed == types.list(value))
        )
    ]


def slice_assignment(lower, upper, step, sliced, value, types):
    """Constraints for slice assignment
    
    Only lists support slice assignments.
    """
    x = Const("x", types.type_sort)
    return [
        And(types.subtype(lower, types.int), types.subtype(upper, types.int), types.subtype(step, types.int),
            Exists([x], And(sliced == types.list(x), value == types.list(x))))
    ]


def delete_subscript(indexed, types):
    """Constraints for subscript deletion
    
    Prevent subscript deletion of tuples, strings and bytes (Immutable sequences)
    """
    return [
        Not(Or(
            indexed == types.string,
            indexed == types.bytes,
            types.subtype(indexed, types.tuple)
        ))
    ]


def body(result, new, types):
    """Constraints for body statements
    
    The body type is the super-type of all its statements, or none if no statement returns type.
    """
    return [
        Implies(new != types.none, types.subtype(new, result))
    ]


def control_flow(then, orelse, result, types):
    """Constraints for control-flow blocks (if/else, while, for)"""
    # TODO numeric casting
    return [
        Implies(orelse == types.none, result == then),
        Implies(orelse != types.none, And(
            types.subtype(then, result),
            types.subtype(orelse, result)
        ))
    ]


def for_loop(iterable, target, types):
    """Constraints for for-loop iterable and iteration target"""
    x = Const("x", types.type_sort)
    return [
        Or(
            iterable == types.list(target),
            iterable == types.set(target),
            Exists([x], iterable == types.dict(target, x), patterns=[types.dict(target, x)]),
            And(iterable == types.string, target == types.string),
            And(iterable == types.bytes, target == types.bytes)
        )
    ]


def try_except(then, orelse, final, result, types):
    """Constraints for try/except block"""
    return [
        types.subtype(then, result),
        types.subtype(orelse, result),
        types.subtype(final, result)
    ]


def instance_axioms(called, args, result, types):
    """Constraints for class instantiation
    
    A class instantiation corresponds to a normal function call to the __init__ function, where
    the return type will be an instance of this class.
    
    The called maybe of any user-defined type in the program, so the call is asserted
    with the __init__ function of every call
    """

    if len(args) + 1 >= len(types.funcs):  # Instantiating a class with more number of args than the max possible number
        return []

    # Assert with __init__ function of all classes in the program
    axioms = []
    for t in types.all_types:
        # Get the instance accessor from the type_sort data type.
        instance = getattr(types.type_sort, "instance")(types.all_types[t])

        # Get the __init__ function of the current class
        init_func = types.attributes[t]["__init__"]

        # Assert that it's a call to this __init__ function
        axioms.append(
            And(called == types.all_types[t],
                result == instance,
                init_func == types.funcs[len(args) + 1]((instance,) + args + (types.none,))))

    return axioms


def function_call_axioms(called, args, result, types):
    """Constraints for function calls
    
    To support default arguments values, an axiom for every possible arguments length is added, provided that the
    defaults count for the function matches the inferred one.
    """
    axioms = []
    for i in range(len(args), len(types.funcs)):  # Only assert with functions with length >= call arguments length
        rem_args = i - len(args)  # The remaining arguments are expected to have default value in the func definition.
        rem_args_types = ()
        for j in range(rem_args):
            arg_idx = len(args) + j + 1
            arg_accessor = getattr(types.type_sort, "func_{}_arg_{}".format(i, arg_idx))  # Get the default arg type
            rem_args_types += (arg_accessor(called),)

        axioms.append(And(called == types.funcs[i](args + rem_args_types + (result,)),
                          types.defaults_count(called) >= len(rem_args_types)))

    return axioms


def call(called, args, result, types):
    """Constraints for calls
    
    Cases:
        - Function call
        - Class instantiation
    """
    return [
        Or(
           function_call_axioms(called, args, result, types) + instance_axioms(called, args, result, types)
        )
    ]


def attribute(instance, attr, result, types):
    """Constraints for attribute access
    
    Assert with all classes having the attribute attr
    """
    axioms = []
    for t in types.all_types:
        if attr in types.attributes[t]:
            type_instance = getattr(types.type_sort, "instance")(types.all_types[t])
            attr_type = types.attributes[t][attr]
            axioms.append(And(instance == type_instance, result == attr_type))
    return Or(axioms)
