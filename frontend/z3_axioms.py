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


def index(indexed, index, result):
    return [
        Or(
            indexed == Dict(index, result),
            And(subtype(index, Int), indexed == List(result))
        )
    ]
