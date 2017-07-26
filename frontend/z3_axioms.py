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
    
    TODO: Tuples addition
    """
    return [
        Or(
            And(types.subtype(left, types.seq), left == right, left == result),
            And(types.subtype(left, types.num), types.subtype(right, left), result == left),
            And(types.subtype(right, types.num), types.subtype(left, right), result == right),

            # result from list addition is a list with a supertype of operands' types
            And(left == types.list(types.list_type(left)),
                right == types.list(types.list_type(right)),
                result == types.list(types.list_type(result)),
                types.subtype(types.list_type(left), types.list_type(result)),
                types.subtype(types.list_type(right), types.list_type(result)),
                ),
            And(left == types.string, right == types.string, result == types.string)
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
            # multiplication of two booleans is an integer. Handle it separately
            And(left == types.bool, right == types.bool, result == types.int),
            And(Or(left != types.bool, right != types.bool),
                Or(
                    And(types.subtype(left, types.seq), types.subtype(right, types.int), result == left),
                    And(types.subtype(left, types.int), types.subtype(right, types.seq), result == right),
                    And(types.subtype(left, types.num), types.subtype(right, left), result == left),
                    And(types.subtype(right, types.num), types.subtype(left, right), result == right),
                    )
                )
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
        And(types.subtype(right, types.num), types.subtype(left, right), result == right),
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
             And(types.subtype(ind, types.int), indexed == types.bytes, result == types.bytes),
             ]
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
            Or(
                sliced == types.string,
                sliced == types.bytes,
                types.subtype(sliced, types.tuple),
                sliced == types.list(types.list_type(sliced))
            ), result == sliced)
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


def subscript_assignment(target, types):
    """Constraints for subscript assignment
    
    Cases:
        - Index assignment
        - Slice assignment
        
    strings, bytes and tuples are immutable objects. i.e., they don't support subscript assignments
    """
    return [
        target != types.string,
        target != types.bytes,
        Not(types.subtype(target, types.tuple))
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
        Implies(new != types.none, result == new)
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


def one_type_instantiation(class_name, args, result, types):
    """Constraints for class instantiation, if the class name is known
    
    :param class_name: The class to be instantiated
    :param args: the types of the arguments passed to the class instantiation
    :param result: The resulting instance from instantiation
    :param types: Z3Types object for this inference program
    """
    init_args_count = types.class_to_init_count[class_name]

    # Get the instance accessor from the type_sort data type.
    instance = getattr(types.type_sort, "instance")(types.all_types[class_name])

    # Get the __init__ function of the this class
    init_func = types.instance_attributes[class_name]["__init__"]

    # Assert that it's a call to this __init__ function

    # Get the default args count
    defaults_accessor = getattr(types.type_sort, "func_{}_defaults_args".format(init_args_count))
    default_count = defaults_accessor(init_func)

    rem_args_count = init_args_count - len(args) - 1
    rem_args = []
    for i in range(rem_args_count):
        arg_idx = len(args) + i + 2
        # Get the default arg type
        arg_accessor = getattr(types.type_sort, "func_{}_arg_{}".format(init_args_count, arg_idx))
        rem_args.append(arg_accessor(init_func))

    all_args = (instance,) + args + tuple(rem_args) + (types.none,)  # The return type of __init__ is None
    z3_func_args = (default_count,) + all_args
    # Assert that it's a call to this __init__ function
    return And(
        result == instance,
        init_func == types.funcs[len(args) + len(rem_args) + 1](z3_func_args), default_count >= rem_args_count)


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
        axioms.append(And(one_type_instantiation(t, args, result, types),
                          called == types.all_types[t]))
    return axioms


def function_call_axioms(called, args, result, types):
    """Constraints for function calls
    
    To support default arguments values, an axiom for every possible arguments length is added, provided that the
    defaults count for the function matches the inferred one.
    """
    axioms = []
    for i in range(len(args), len(types.funcs)):  # Only assert with functions with length >= call arguments length
        rem_args = i - len(args)  # The remaining arguments are expected to have default value in the func definition.
        if rem_args > types.config.max_default_args:
            break
        rem_args_types = ()
        for j in range(rem_args):
            arg_idx = len(args) + j + 1
            arg_accessor = getattr(types.type_sort, "func_{}_arg_{}".format(i, arg_idx))  # Get the default arg type
            rem_args_types += (arg_accessor(called),)

        # Get the default args count accessor
        defaults_accessor = getattr(types.type_sort, "func_{}_defaults_args".format(i))
        defaults_count = defaults_accessor(called)
        # Add the axioms for function call, default args count, and arguments subtyping.
        axioms.append(And(called == types.funcs[i]((defaults_accessor(called),) + tuple(args) + rem_args_types + (result,)),

                          defaults_count >= rem_args,
                          defaults_count <= types.config.max_default_args))
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
        if attr in types.instance_attributes[t]:
            # instance access. Ex: A().x
            type_instance = getattr(types.type_sort, "instance")(types.all_types[t])
            attr_type = types.instance_attributes[t][attr]
            axioms.append(And(instance == type_instance, result == attr_type))
        if attr in types.class_attributes[t]:
            # class access. Ex: A.x
            class_type = types.all_types[t]
            attr_type = types.class_attributes[t][attr]
            axioms.append(And(instance == class_type, result == attr_type))

    return Or(axioms)
