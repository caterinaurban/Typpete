from frontend.z3_types import And, Or, Implies, Not


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
            And(types.subtype(left, types.seq), left == right, left == result),
            And(types.subtype(left, types.num), types.subtype(right, left), result == left),
            And(types.subtype(left, types.num), types.subtype(left, right), result == right),
        ),
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
            And(types.subtype(left, types.num), types.subtype(right, left), result == left),
            And(types.subtype(left, types.num), types.subtype(left, right), result == right),
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


def arithmetic(left, right, result, is_mod, types):
    """Constraints for arithmetic operation

    Cases:
        - Number_1 (op) Number_2 --> Stronger(Number_1, Number_2)
        - String formatting
        
    Ex:
        - 2 ** 3.0
        - 3 - 4
        - "Case #%i: %i" % (u, v)
    """
    axioms = [
        And(types.subtype(left, types.num), types.subtype(right, left), result == left),
        And(types.subtype(left, types.num), types.subtype(left, right), result == right),
    ]

    if is_mod:
        axioms += [And(Or(left == types.string, left == types.bytes), result == left)]

    return [Or(axioms)]


def bitwise(left, right, result, types):
    """Constraints for arithmetic operation

    Cases:
        - (Number_1: Int/Bool) (op) (Number_2: Int/Bool) --> Stronger(Number_1, Number_2)
        
    Ex:
        - 1 & 2
        - True ^ False
    """
    return arithmetic(left, right, result, False, types) + [
        And(types.subtype(left, types.int), types.subtype(right, types.int))]


def bool_op(values, result, types):
    """Constrains for boolean operations (and/or)
    
    The result is the supertype (or numerically stronger) of all operands.
     
    Ex:
        - 2 and str --> object
        - False or 1 --> int
    """
    return [types.subtype(x, result) for x in values]


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
    for cur_len in range(1, len(types.tuples)):
        tuple_args = [getattr(types.type_sort, "tuple_{}_arg_{}".format(cur_len, i + 1))(indexed)
                      for i in range(cur_len)]
        t.append(And(
            indexed == types.tuples[cur_len](*tuple_args),
            *[types.subtype(x, result) for x in tuple_args]
        ))

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
    return [
        Or(
            iterable == types.list(target),
            iterable == types.set(target),
            And(iterable == types.string, target == types.string),
            And(iterable == types.bytes, target == types.bytes),
            iterable == types.dict(target, types.dict_value_type(iterable)),
        )
    ]


def assignment(target, value, types):
    """Constraints for variable assignment.
    
    The left hand side is either a super type or a numerically stronger type of the right hand side.
    """
    return [
        types.subtype(value, target)
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

    # tuple multiple assignment:
    # Assert with tuples of different lengths, maintaining the correct position of the target in the tuple.
    t = []
    for cur_len in range(position + 1, len(types.tuples)):

        before_target = [getattr(types.type_sort, "tuple_{}_arg_{}".format(cur_len, i + 1))(value)
                         for i in range(position)]  # The tuple elements before the target
        after_target = [getattr(types.type_sort, "tuple_{}_arg_{}".format(cur_len, i + 1))(value)
                        for i in range(position + 1, cur_len)]  # The tuple elements after the target

        params = before_target + [target] + after_target  # The parameters to instantiate the tuple

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
    return [
        And(types.subtype(lower, types.int), types.subtype(upper, types.int), types.subtype(step, types.int),
            sliced == types.list(types.list_type(sliced)), value == sliced)
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
    return [
        Or(
            iterable == types.list(target),
            iterable == types.set(target),
            iterable == types.dict(target, types.dict_value_type(iterable)),
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


def func_call(called, args, result, types):
    if len(args) == 0:
        return called == types.funcs[0](result)

    subtype_axioms = []
    z3_args = []
    for i in range(len(args)):
        z3_arg = getattr(types.type_sort, "func_{}_arg_{}".format(len(args), i + 1))(called)
        z3_args.append(z3_arg)
        arg = args[i]
        subtype_axioms.append(types.subtype(arg, z3_arg))

    func_type = types.funcs[len(args)]
    z3_args.append(result)
    return And(subtype_axioms + [called == func_type(*z3_args)])


def call(called, args, result, types):
    """Constraints for calls
    
    Cases:
        - Function call
        - Class instantiation
    """
    return [
        Or(
            [func_call(called, args, result, types)] + instance_axioms(called, args, result, types)
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
