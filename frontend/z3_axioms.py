from frontend.z3_types import *


def add(left, right, result):
    return [
        Or(
            And(subtype(left, Num), subtype(right, Num), subtype(result, Num)),
            And(subtype(left, Seq), left == right, left == result)
        ),

        Implies(And(subtype(left, Num), stronger_num(left, right)), result == left),
        Implies(And(subtype(left, Num), stronger_num(right, left)), result == right)
    ]


def mult(left, right, result):
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
    return [
        And(subtype(left, Num), subtype(right, Num)),
        Implies(Or(left == Complex, right == Complex), result == Complex),
        Implies(Not(Or(left == Complex, right == Complex)), result == Float)
    ]


def arithmetic(left, right, result):
    return [
        And(subtype(left, Num), subtype(right, Num)),
        Implies(stronger_num(left, right), result == left),
        Implies(stronger_num(right, left), result == right)
    ]


def bitwise(left, right, result):
    return arithmetic(left, right, result) + [And(subtype(left, Int), subtype(right, Int))]


def unary_invert(unary):
    return [
        subtype(unary, Int)
    ]


def unary_other(unary, result):
    return [
        subtype(unary, Num),
        Implies(unary == Bool, result == Int),
        Implies(unary != Bool, result == unary)
    ]


def if_expr(a, b, result):
    return [
        subtype(a, result),
        subtype(b, result)
    ]


def index(indexed, index, result):
    # TODO tuples
    return [
        Or(
            indexed == Dict(index, result),
            And(subtype(index, Int), indexed == List(result))
        )
    ]


def slice(lower, upper, step, sliced, result):
    # TODO tuples
    return [
        And(subtype(lower, Int), subtype(upper, Int), subtype(step, Int), subtype(sliced, Seq), result == sliced)
    ]


def generator(iter, target):
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
    return [
        Implies(subtype(target, Num), And(subtype(value, Num), stronger_num(target, value))),
        Implies(Not(subtype(target, Num)), subtype(value, target))
    ]


def index_assignment(indexed, index, value):
    return [
        Or(
            indexed == Dict(index, value),
            And(subtype(index, Int), indexed == List(value))
        )
    ]


def slice_assignment(lower, upper, step, sliced, value):
    return [
        And(subtype(lower, Int), subtype(upper, Int), subtype(step, Int), subtype(sliced, Seq),
            Exists([x], And(sliced == List(x), value == List(x))))
    ]


def delete_subscript(indexed):
    return [
        Not(Or(
            indexed == String,
            indexed == Bytes,
            subtype(indexed, Tuple)
        ))
    ]


def body(result, new):
    return [
        Implies(new != zNone, subtype(new, result))
    ]


def control_flow(body, orelse, result):
    # TODO numeric casting
    return [
        And(
            subtype(body, result),
            subtype(orelse, result)
        )
    ]
