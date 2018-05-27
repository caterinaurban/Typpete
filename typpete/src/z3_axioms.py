from typpete.src.constants import ALIASES
from typpete.src.z3_types import And, Or, Implies, Not


def overloading_axioms(left, right, result, method_name, types):
    """
    Constraints for operator overloading
    
    :param left: The left operand of the operation 
    :param right: The right operand of the operation
    :param result: The result of the operation
    :param method_name: The name of the magic method responsible for overloading the operation. e.g., __add__
    :param types: the Z3Types object
    :return: axioms of the operator overloading
    """
    axioms = []
    for t in types.all_types:
        # Check that `method_name` is a method in the current class.
        if method_name in types.class_to_funcs[t]:
            method_type = types.instance_attributes[t][method_name]

            # the left operand is the instance
            instance = getattr(types.type_sort, "type_arg_0")(types.all_types[t])

            # the right operand is a subtype of the `other` arg in the magic method
            other_type = getattr(types.type_sort, "func_2_arg_2")(method_type)

            # the result is the return type of the magic method
            return_type = getattr(types.type_sort, "func_2_return")(method_type)
            axioms.append(And(left == instance, types.subtype(right, other_type), result == return_type))
    return axioms


def comparison_axioms(left, right, method_name, types):
    """
    Constraints for ordering comparison (>, >=, <, <=)
    """
    return [
        And(left != types.none, right != types.none),
        Or([
            And(types.subtype(left, types.float), types.subtype(right, types.float)),
            And(left == types.list(types.list_type(left)), right == left),
            And(left == types.set(types.set_type(left)), right == types.set(types.set_type(right))),
            And(types.subtype(left, types.tuple), types.subtype(right, types.tuple)),
            And(left == types.string, right == types.string),
            And(left == types.bytes, right == types.bytes),
        ]
        + overloading_axioms(left, right, types.bool, method_name, types)
        )
    ]



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
        And(left != types.none, right != types.none),
        Or([
               And(types.subtype(left, types.complex), types.subtype(right, left), result == left),
               And(types.subtype(right, types.complex), types.subtype(left, right), result == right),
               And(types.subtype(left, types.seq), left == right, left == result),

               And(left == types.list(types.list_type(left)),
                   right == left,
                   result == left,
                   ),
               And(left == types.string, right == types.string, result == types.string)
           ]
           + overloading_axioms(left, right, result, "__add__", types)
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
        And(left != types.none, right != types.none),
        Or([
            # multiplication of two booleans is an integer. Handle it separately
            And(left == types.bool, right == types.bool, result == types.int),
            And(Or(left != types.bool, right != types.bool),
                Or(
                    And(types.subtype(left, types.seq), types.subtype(right, types.int), result == left),
                    And(types.subtype(left, types.int), types.subtype(right, types.seq), result == right),

                    And(types.subtype(left, types.complex), types.subtype(right, left), result == left),
                    And(types.subtype(right, types.complex), types.subtype(left, right), result == right),
                    )
                )
            ]
           + overloading_axioms(left, right, result, "__mul__", types)
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
        And(left != types.none, right != types.none),
        And(types.subtype(left, types.complex), types.subtype(right, types.complex)),
        Implies(Or(left == types.complex, right == types.complex), result == types.complex),
        Implies(Not(Or(left == types.complex, right == types.complex)), result == types.float)
    ]


def arithmetic(left, right, result, magic_method, is_mod, types):
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
        And(types.subtype(left, types.complex), types.subtype(right, left), result == left),
        And(types.subtype(right, types.complex), types.subtype(left, right), result == right),
    ] + overloading_axioms(left, right, result, magic_method, types)

    if is_mod:
        axioms += [And(Or(left == types.string, left == types.bytes), result == left)]

    return [
        And(left != types.none, right != types.none),
        Or(axioms)
    ]


def bitwise(left, right, result, magic_method, types):
    """Constraints for arithmetic operation

    Cases:
        - (Number_1: Int/Bool) (op) (Number_2: Int/Bool) --> Stronger(Number_1, Number_2)
        
    Ex:
        - 1 & 2
        - True ^ False
    """
    return arithmetic(left, right, result, magic_method, False, types) + [
            Implies(And(types.subtype(left, types.complex), types.subtype(right, types.complex)),
                    types.subtype(left, types.int), types.subtype(right, types.int))]


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
        types.subtype(unary, types.int),
        unary != types.none
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
        unary != types.none,
        types.subtype(unary, types.complex),
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

    t.extend(overloading_axioms(indexed, ind, result, '__getitem__', types))

    return [
        Or(
            [And(indexed == types.dict(types.dict_key_type(indexed), result),
                 types.subtype(ind, types.dict_key_type(indexed))),
             And(types.subtype(ind, types.int), indexed == types.list(result)),
             And(types.subtype(ind, types.int), indexed == types.string, result == types.string),
             And(types.subtype(ind, types.int), indexed == types.bytes, result == types.bytes),
             ]
            + t
        )
    ], Or(
            [indexed == types.dict(ind, result),
             And(ind == types.int, indexed == types.list(result)),
             And(ind == types.int, indexed == types.string, result == types.string),
             And(ind == types.int, indexed == types.bytes, result == types.bytes),
             ]
        )


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


def one_type_instantiation(class_name, args, result, types, tvs):
    """Constraints for class instantiation, if the class name is known
    
    :param class_name: The class to be instantiated
    :param args: the types of the arguments passed to the class instantiation
    :param result: The resulting instance from instantiation
    :param types: Z3Types object for this inference program
    """
    if class_name in types.abstract_types:
        return Or()
    init_args_count = types.class_to_funcs[class_name]["__init__"][0]

    # Get the __init__ function of the this class
    init_func = types.instance_attributes[class_name]["__init__"]

    if class_name not in types.config.class_type_params:

        # Get the instance accessor from the type_sort data type.
        instance = getattr(types.type_sort, "type_arg_0")(types.all_types[class_name])



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
        return And(
                  result == instance,
                  init_func == types.funcs[len(args) + len(rem_args) + 1](z3_func_args), default_count >= rem_args_count)
    else:


        rec_type = types.classes[class_name](tvs[:len(types.config.class_type_params[class_name])])
        generic_receiver_type = result == rec_type
        generic_args = (rec_type,) + args
        # Assert that it's a call to this __init__ function
        return And(generic_receiver_type, Or(*generic_call_axioms(init_func, generic_args, types.none, types, tvs)))



def instance_axioms(called, args, result, types, tvs):
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
        if t in types.config.class_type_params:
            continue
        axioms.append(And(one_type_instantiation(t, args, result, types, tvs),
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
        axiom = And(called == types.funcs[i]((defaults_accessor(called),) + tuple(args) + rem_args_types + (result,)),
                    defaults_count >= rem_args)
        axioms.append(axiom)
    return axioms


def generic_call_axioms(called, args, result, types, tvs):
    axioms = []
    to_iterate_over = range(types.config.max_type_args)
    for i in to_iterate_over:
        generic_constr = types.generics[i]
        cargs = []
        for j in range(i + 1):
            cargs.append(getattr(types, 'generic{}_tv{}'.format(i + 1, j + 1))(called))
        is_generic = called == generic_constr(*cargs, getattr(types, 'generic{}_func'.format(i + 1))(called))

        under_upper = []
        for k, ta in enumerate(tvs):
            if not k <= i:
                break
            current_tv = getattr(types, 'generic{}_tv{}'.format(i + 1, k + 1))(called)
            def mysubst(a):
                res = a
                for l in range(k):
                    res = types.subst(res, cargs[l], tvs[l])
                return res
            under_upper.append(types.subtype(ta, mysubst(types.upper(current_tv))))

        def mysubst(a):
            res = a
            for arg, tv in zip(cargs, tvs):
                res = types.subst(res, arg, tv)
            return res

        called_func = getattr(types, 'generic{}_func'.format(i + 1))(called)


        ##
        for i in range(len(args), len(types.funcs)):  # Only assert with functions with length >= call arguments length
            rem_args = i - len(args)  # The remaining arguments are expected to have default value in the func definition.
            if rem_args > types.config.max_default_args:
                break
            rem_args_types = ()
            for j in range(rem_args):
                arg_idx = len(args) + j + 1
                arg_accessor = getattr(types.type_sort, "func_{}_arg_{}".format(i, arg_idx))  # Get the default arg type
                rem_args_types += (arg_accessor(called_func),)

            all_args = tuple(args) + rem_args_types

            # Get the default args count accessor
            defaults_accessor = getattr(types.type_sort,
                                        "func_{}_defaults_args".format(i))
            defaults_count = defaults_accessor(called_func)
            if len(all_args) == 0:
                axiom = mysubst(called_func) == types.funcs[0](0, result)
                axioms.append(And(is_generic, axiom))
            else:
                subtype_axioms = []
                z3_args = []
                for i in range(len(all_args)):
                    z3_arg = mysubst(getattr(types.type_sort,
                                             "func_{}_arg_{}".format(len(all_args), i + 1))(called_func))
                    z3_args.append(z3_arg)
                    if i < len(args):
                        arg = args[i]
                        subtype_axioms.append(types.subtype(arg, z3_arg))

                func_type = types.funcs[len(all_args)]
                z3_args.append(result)
                res = And(subtype_axioms + [mysubst(called_func) == func_type(defaults_count, *z3_args), defaults_count >= rem_args])
                axiom = And(is_generic, *under_upper, res)
                axioms.append(axiom)

    return axioms


def call(called, args, result, types, tvs):
    """Constraints for calls
    
    Cases:
        - Function call
        - Class instantiation
        - Callable classes
    """
    r1 = function_call_axioms(called, args, result, types)
    r2 = instance_axioms(called, args, result, types, tvs)
    r3 = class_call_axioms(called, args, result, types)
    r4 = generic_call_axioms(called, args, result, types, tvs)
    return [
        Or(
            (r1
             + r2
             + r3
             + r4)
        )
    ]


def class_call_axioms(called, args, result, types):
    """Constraints for callable classes
    
    Assert with all classes which have the method `__call__`.
    """
    axioms = []
    for t in types.all_types:
        # Check that `__call__` is a method in the current class.
        if "__call__" in types.class_to_funcs[t]:
            call_type = types.instance_attributes[t]["__call__"]
            instance = getattr(types.type_sort, "type_arg_0")(types.all_types[t])
            args_types = (instance,) + args
            axioms.append(And(called == instance,
                              Or(function_call_axioms(call_type, args_types, result, types))))
    return axioms


def staticmethod_call(class_type, args, result, attr, types):
    """Constraints for staticmethod calls
    
    Assert with all classes which has the method `attr` which has decorator `staticmethod`
    """
    axioms = []
    for t in types.all_types:
        # Check that attr is a method and "staticmethod" is one of its decorators
        if attr in types.class_to_funcs[t]:
            decorators = types.class_to_funcs[t][attr][1]
            if "staticmethod" in decorators:
                attr_type = types.instance_attributes[t][attr]
                axioms.append(And(class_type == types.all_types[t],
                                  Or(function_call_axioms(attr_type, args, result, types))))
    return axioms


def instancemethod_call(instance, args, result, attr, types, tvs):
    """Constraints for calls on instances

    There are two cases:
    - The called is an instance method
    - The called is a normal instance attribute which happens to be callable

    In the first case, check that it appears in the class instance methods and is not static method
    In the second case, check that it does not appear in the class instance methods but appears in the
        class attributes
        
    Add the receiver argument in the first case only
    `
    """
    axioms = []
    for t in types.all_types:
        # Check that attr is an instance method and "staticmethod" is not of its decorators,
        # if so, add call axioms with a receiver
        if attr in types.class_to_funcs[t]:
            decorators = types.class_to_funcs[t][attr][1]
            if "staticmethod" not in decorators and "property" not in decorators:
                attr_type = types.instance_attributes[t][attr]

                receiver_subtype = False
                if t in types.config.class_type_params:
                    type_func = types.classes[t] if t not in ALIASES else getattr(types.type_sort, ALIASES[t])
                    rec_type = type_func(tvs[:len(types.config.class_type_params[t])])
                    receiver_subtype = types.subtype(instance, rec_type)
                    axioms.append(And(receiver_subtype, Or(*generic_call_axioms(attr_type, list(args), result, types, tvs))))
                else:
                    axioms.append(And(instance == types.type_sort.type_arg_0(types.all_types[t]),
                                     Or(function_call_axioms(attr_type, args, result, types))),
                                 )

        # Otherwise, check if it is an instance attribute, if so add call axioms with no receiver
        elif attr in types.instance_attributes[t]:
            attr_type = types.instance_attributes[t][attr]
            axioms.append(And(instance == types.type_sort.type_arg_0(types.all_types[t]),
                              Or(function_call_axioms(attr_type, args[1:], result, types) + class_call_axioms(attr_type, args[1:], result, types))))
    return axioms


def attribute(instance, attr, result, types):
    """Constraints for attribute access
    
    Assert with all classes having the attribute attr
    """
    axioms = []
    for t in types.all_types:
        if t in types.instance_attributes and attr in types.instance_attributes[t]:
            # instance access. Ex: A().x
            attr_type = types.instance_attributes[t][attr]
            if t in types.config.class_type_params:
                tps = types.config.class_type_params[t]
                accessors = [ctb[1:] for ctb in types.config.class_to_base
                             if isinstance(ctb, tuple) and ctb[0] == t]
                accessors = accessors[0]
                args = [getattr(types.type_sort, a)(instance) for a in accessors]
                params = [getattr(types, "generic{}_tv{}".format(len(tps), i+1))(attr_type)
                          for i, _ in enumerate(tps)]
                gen_func = getattr(types, "generic{}_func".format(len(tps)))(attr_type)

                generic_attr_type = getattr(types.type_sort, 'is_generic{}'.format(len(tps)))(attr_type)

                type_instance = types.classes[t](args)
                substituted = gen_func
                for arg, param in zip(args, params):
                    substituted = types.subst(substituted, param, arg)
                axioms.append(And(instance == type_instance, generic_attr_type, result == substituted))
                continue
            type_instance = getattr(types.type_sort, "type_arg_0")(types.all_types[t])

            # Check if it is a property access
            if attr in types.class_to_funcs[t] and "property" in \
                    types.class_to_funcs[t][attr][1]:
                # Set the attribute type to be the return type of the property method
                method_type = types.instance_attributes[t][attr]
                arg_accessor = getattr(types.type_sort, "func_1_arg_1")
                axioms.append(And(instance == type_instance,
                                  method_type == types.funcs[1](0,
                                                                arg_accessor(method_type),
                                                                result)))
            else:
                attr_type = types.instance_attributes[t][attr]
                axioms.append(And(instance == type_instance, result == attr_type))
        if t in types.class_attributes and attr in types.class_attributes[t]:
            # class access. Ex: A.x
            class_type = types.all_types[t]
            attr_type = types.class_attributes[t][attr]
            axioms.append(And(instance == class_type, result == attr_type))
    return Or(axioms)
