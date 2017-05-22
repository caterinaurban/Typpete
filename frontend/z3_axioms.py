from frontend.z3_types import *


def add(left, right, result):
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
            And(subtype(left, Num), subtype(right, Num), subtype(result, Num)),
            And(subtype(left, Seq), left == right, left == result)
        ),

        Implies(And(subtype(left, Num), stronger_num(left, right)), result == left),
        Implies(And(subtype(left, Num), stronger_num(right, left)), result == right)
    ]


def mult(left, right, result):
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
            And(subtype(left, Int), subtype(right, Seq), result == right),
            And(subtype(left, Seq), subtype(right, Int), result == left),
            And(subtype(left, Num), subtype(right, Num), subtype(result, Num))
        ),

        Implies(
            And(subtype(left, Num), subtype(right, Num), stronger_num(left, right)),
            result == left
        ),

        Implies(
            And(subtype(left, Num), subtype(right, Num), stronger_num(right, left)),
            result == right
        )
    ]


def div(left, right, result):
    """Constraints for the division operation

    Cases:
        - Number_1 / Number_2 --> Stronger(Float, Stronger(Number_1, Number2))
        
    Ex:
        - True / 7
        - 3 / (1 + 2j)
    """
    return [
        And(subtype(left, Num), subtype(right, Num)),
        Implies(Or(left == Complex, right == Complex), result == Complex),
        Implies(Not(Or(left == Complex, right == Complex)), result == Float)
    ]


def arithmetic(left, right, result):
    """Constraints for arithmetic operation

    Cases:
        - Number_1 (op) Number_2 --> Stronger(Number_1, Number_2)
        
    Ex:
        - 2 ** 3.0
        - 3 - 4
    """
    return [
        And(subtype(left, Num), subtype(right, Num)),
        Implies(stronger_num(left, right), result == left),
        Implies(stronger_num(right, left), result == right)
    ]


def bitwise(left, right, result):
    """Constraints for arithmetic operation

    Cases:
        - (Number_1: Int/Bool) (op) (Number_2: Int/Bool) --> Stronger(Number_1, Number_2)
        
    Ex:
        - 1 & 2
        - True ^ False
    """
    return arithmetic(left, right, result) + [And(subtype(left, Int), subtype(right, Int))]


def unary_invert(unary):
    """Constraints for the invert unary operation
    
    Only subtypes for int are eligible for this operation (No floats)
    
    Ex:
    - ~231
    """
    return [
        subtype(unary, Int)
    ]


def unary_other(unary, result):
    """Constraints for any unary operation except (~) and (not)
    
    Cases:
        - (op) Number --> Stronger(Int, Number)
        
    Ex:
        - -True
        - +2.0
    """
    return [
        subtype(unary, Num),
        Implies(unary == Bool, result == Int),
        Implies(unary != Bool, result == unary)
    ]


def if_expr(a, b, result):
    """Constraints for if expressions
    
    Cases:
        - (a) if (TEST) else (b) --> Super(a, b)
    """
    return [
        subtype(a, result),
        subtype(b, result)
    ]


def index(indexed, index, result):
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
    quantifiers_consts = [Const("tuples_q_{}".format(x), type_sort) for x in range(len(Tuples) - 1)]
    for cur_len in range(1, len(Tuples)):
        quants = quantifiers_consts[:cur_len]
        t.append(Exists(quants, And(
            indexed == Tuples[cur_len](*quants),
            *[subtype(x, result) for x in quants]
        ), patterns=[Tuples[cur_len](*quants)]))

    return [
        Or(
            [indexed == Dict(index, result),
             And(subtype(index, Int), indexed == List(result)),
             And(subtype(index, Int), indexed == String, result == String),
             And(subtype(index, Int), indexed == Bytes, result == Bytes)]
            + t
        )
    ]


def slice(lower, upper, step, sliced, result):
    """Constraints for slicing subscript
    
    Cases:
        - Sequence --> Sequence
    """
    return [
        And(subtype(lower, Int), subtype(upper, Int), subtype(step, Int), subtype(sliced, Seq), result == sliced)
    ]


def generator(iter, target):
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
            iter == List(target),
            iter == Set(target),
            And(iter == String, target == String),
            And(iter == Bytes, target == Bytes),
            Exists(x, iter == Dict(target, x), patterns=[Dict(target, x)])
        )
    ]


def assignment(target, value):
    """Constraints for variable assignment.
    
    The left hand side is either a super type or a numerically stronger type of the right hand side.
    """
    return [
        Implies(subtype(target, Num), And(subtype(value, Num), stronger_num(target, value))),
        Implies(Not(subtype(target, Num)), subtype(value, target))
    ]


def multiple_assignment(target, value, position):
    """Constraints for multiple assignments
    
    :param target: The type of the assignment target (LHS)
    :param value: The type of the assignment value (RHS)
    :param position: The position of the target/value in the multiple assignment
    
    Cases:
        - List: a, b = [1, 2]
        - Tuple: a, b = 1, "string"
        
    Ex:
        - a, b = [1, 2]
        
        The above example calls this function twice:
            * first time: target := type(a), value := type(1), position := 0
            * second time: target := type(b), value := type(2), position := 1
    """

    # List multiple assignment
    lst = [value == List(target)]

    # Tuple multiple assignment:
    # Assert with tuples of different lengths, maintaining the correct position of the target in the tuple.
    t = []
    quantifiers_consts = [Const("tuples_q_{}".format(x), type_sort) for x in range(len(Tuples) - 2)]
    for cur_len in range(position + 1, len(Tuples)):
        before_target = quantifiers_consts[:position]  # The tuple elements before the target
        after_target = quantifiers_consts[position:cur_len - 1]  # The tuple elements after the target
        quants = before_target + after_target  # The quantifiers constants for this tuple length
        params = before_target + [target] + after_target  # The parameters to instantiate the tuple

        if quants:
            t.append(Exists(quants, value == Tuples[cur_len](*params), patterns=[Tuples[cur_len](*params)]))
        else:
            t.append(value == Tuples[cur_len](*params))

    return [Or(lst + t)]


def index_assignment(indexed, index, value):
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
            indexed == Dict(index, value),
            And(subtype(index, Int), indexed == List(value))
        )
    ]


def slice_assignment(lower, upper, step, sliced, value):
    """Constraints for slice assignment
    
    Only lists support slice assignments.
    """
    return [
        And(subtype(lower, Int), subtype(upper, Int), subtype(step, Int),
            Exists([x], And(sliced == List(x), value == List(x))))
    ]


def delete_subscript(indexed):
    """Constraints for subscript deletion
    
    Prevent subscript deletion of tuples, strings and bytes (Immutable sequences)
    """
    return [
        Not(Or(
            indexed == String,
            indexed == Bytes,
            subtype(indexed, Tuple)
        ))
    ]


def body(result, new):
    """Constraints for body statements
    
    The body type is the super-type of all its statements, or none if no statement returns type.
    """
    return [
        Implies(new != zNone, subtype(new, result))
    ]


def control_flow(body, orelse, result):
    """Constraints for control-flow blocks (if/else, while, for)"""
    # TODO numeric casting
    return [
        Implies(orelse == zNone, result == body),
        Implies(orelse != zNone, And(
            subtype(body, result),
            subtype(orelse, result)
        ))
    ]


def for_loop(iterable, target):
    """Constraints for for-loop iterable and iteration target"""
    return [
        Or(
            iterable == List(target),
            iterable == Set(target),
            Exists([x], iterable == Dict(target, x), patterns=[Dict(target, x)]),
            And(iterable == String, target == String),
            And(iterable == Bytes, target == Bytes)
        )
    ]


def try_except(body, orelse, final, result):
    """Constraints for try/except block"""
    return [
        subtype(body, result),
        subtype(orelse, result),
        subtype(final, result)
    ]


def instance_axioms(called, args, result):
    """Constraints for class instantiation"""

    if len(args) + 1 >= len(Funcs):  # Instantiating a class with more number of args than the max possible number
        return []

    # Assert with __init__ function of all classes in the program
    axioms = []
    for t in all_types:
        instance = getattr(type_sort, "instance")(all_types[t])
        init_func = Attributes[t]["__init__"]
        axioms.append(
            And(called == all_types[t],
                result == instance,
                init_func == Funcs[len(args) + 1]((instance,) + args + (zNone,))))

    return axioms


def call(called, args, result):
    """Constraints for calls
    
    Cases:
        - Function call
        - Class instantiation
    """
    return [
        Or(
            [called == Funcs[len(args)](args + (result,))] + instance_axioms(called, args, result)
        )
    ]


def attribute(instance, attr, result):
    """Constraints for attribute access
    
    Assert with all classes having the attribute attr
    """
    axioms = []
    for t in all_types:
        if attr in Attributes[t]:
            type_instance = getattr(type_sort, "instance")(all_types[t])
            attr_type = Attributes[t][attr]
            axioms.append(And(instance == type_instance, result == attr_type))
    return Or(axioms)
