"""The type-system for Python 3 encoded in Z3.

Limitations:
    - The tuples have a maximum size of 5 elements.
    - Function calls can have no more than 5 arguments.
    - Multiple inheritance is not supported.
    - Functions with generic type variables are not supported.
"""
from z3 import *

# ----------- Declare the types data-type -----------

type_sort = Datatype("Type")
type_sort.declare("object")

type_sort.declare("none")

type_sort.declare("number")
type_sort.declare("complex")
type_sort.declare("float")
type_sort.declare("int")
type_sort.declare("bool")

type_sort.declare("sequence")
type_sort.declare("str")
type_sort.declare("bytes")
type_sort.declare("list", ("list_type", type_sort))

type_sort.declare("set", ("set_type", type_sort))
type_sort.declare("dict", ("dict_key_type", type_sort), ("dict_value_type", type_sort))

type_sort.declare("tuple")
type_sort.declare("tuple_1", ("tuple_1_arg_1", type_sort))
type_sort.declare("tuple_2", ("tuple_2_arg_1", type_sort), ("tuple_2_arg_2", type_sort))
type_sort.declare("tuple_3", ("tuple_3_arg_1", type_sort), ("tuple_3_arg_2", type_sort), ("tuple_3_arg_3", type_sort))
type_sort.declare("tuple_4", ("tuple_4_arg_1", type_sort), ("tuple_4_arg_2", type_sort), ("tuple_4_arg_3", type_sort),
                  ("tuple_4_arg_4", type_sort))
type_sort.declare("tuple_5", ("tuple_5_arg_1", type_sort), ("tuple_5_arg_2", type_sort), ("tuple_5_arg_3", type_sort),
                  ("tuple_5_arg_4", type_sort), ("tuple_5_arg_5", type_sort))

type_sort.declare("func")
type_sort.declare("func_0", ("func_0_return", type_sort))
type_sort.declare("func_1", ("func_1_arg_1", type_sort), ("func_1_return", type_sort))
type_sort.declare("func_2", ("func_2_arg_1", type_sort), ("func_2_arg_2", type_sort), ("func_2_return", type_sort))
type_sort.declare("func_3", ("func_3_arg_1", type_sort), ("func_3_arg_2", type_sort), ("func_3_arg_3", type_sort),
                  ("func_3_return", type_sort))
type_sort.declare("func_4", ("func_4_arg_1", type_sort), ("func_4_arg_2", type_sort), ("func_4_arg_3", type_sort),
                  ("func_4_arg_4", type_sort), ("func_4_return", type_sort))
type_sort.declare("func_5", ("func_5_arg_1", type_sort), ("func_5_arg_2", type_sort), ("func_5_arg_3", type_sort),
                  ("func_5_arg_4", type_sort), ("func_5_arg_5", type_sort), ("func_5_return", type_sort))

type_sort = type_sort.create()

# ----------- Get the accessors -----------

Object = type_sort.object

zNone = type_sort.none

Num = type_sort.number
Complex = type_sort.complex
Float = type_sort.float
Int = type_sort.int
Bool = type_sort.bool

Seq = type_sort.sequence
String = type_sort.str
Bytes = type_sort.bytes
List = type_sort.list
list_type = type_sort.list_type

Set = type_sort.set
set_type = type_sort.set_type

Dict = type_sort.dict
dict_key_type = type_sort.dict_key_type
dict_value_type = type_sort.dict_value_type

Tuple = type_sort.tuple
Tuple1 = type_sort.tuple_1
Tuple2 = type_sort.tuple_2
Tuple3 = type_sort.tuple_3
Tuple4 = type_sort.tuple_4
Tuple5 = type_sort.tuple_5

tuple_1_arg_1 = type_sort.tuple_1_arg_1
tuple_2_arg_1 = type_sort.tuple_2_arg_1
tuple_2_arg_2 = type_sort.tuple_2_arg_2
tuple_3_arg_1 = type_sort.tuple_3_arg_1
tuple_3_arg_2 = type_sort.tuple_3_arg_2
tuple_3_arg_3 = type_sort.tuple_3_arg_3
tuple_4_arg_1 = type_sort.tuple_4_arg_1
tuple_4_arg_2 = type_sort.tuple_4_arg_2
tuple_4_arg_3 = type_sort.tuple_4_arg_3
tuple_4_arg_4 = type_sort.tuple_4_arg_4
tuple_5_arg_1 = type_sort.tuple_5_arg_1
tuple_5_arg_2 = type_sort.tuple_5_arg_2
tuple_5_arg_3 = type_sort.tuple_5_arg_3
tuple_5_arg_4 = type_sort.tuple_5_arg_4
tuple_5_arg_5 = type_sort.tuple_5_arg_5

Func = type_sort.func
Func0 = type_sort.func_0
Func1 = type_sort.func_1
Func2 = type_sort.func_2
Func3 = type_sort.func_3
Func4 = type_sort.func_4
Func5 = type_sort.func_5

func_1_arg_1 = type_sort.func_1_arg_1
func_2_arg_1 = type_sort.func_2_arg_1
func_2_arg_2 = type_sort.func_2_arg_2
func_3_arg_1 = type_sort.func_3_arg_1
func_3_arg_2 = type_sort.func_3_arg_2
func_3_arg_3 = type_sort.func_3_arg_3
func_4_arg_1 = type_sort.func_4_arg_1
func_4_arg_2 = type_sort.func_4_arg_2
func_4_arg_3 = type_sort.func_4_arg_3
func_4_arg_4 = type_sort.func_4_arg_4
func_5_arg_1 = type_sort.func_5_arg_1
func_5_arg_2 = type_sort.func_5_arg_2
func_5_arg_3 = type_sort.func_5_arg_3
func_5_arg_4 = type_sort.func_5_arg_4
func_5_arg_5 = type_sort.func_5_arg_5

func_0_return = type_sort.func_0_return
func_1_return = type_sort.func_1_return
func_2_return = type_sort.func_2_return
func_3_return = type_sort.func_3_return
func_4_return = type_sort.func_4_return
func_5_return = type_sort.func_5_return

# ----------- Encode subtyping relationships -----------

subtype = Function("subtype", type_sort, type_sort, BoolSort())
extends = Function("extends", type_sort, type_sort, BoolSort())
not_subtype = Function("not subtype", type_sort, type_sort, BoolSort())
stronger_num = Function("stronger num", type_sort, type_sort, BoolSort())

x = Const("x", type_sort)
y = Const("y", type_sort)
z = Const("z", type_sort)
l = Const("l", type_sort)
m = Const("m", type_sort)
n = Const("n", type_sort)

subtype_properties = [
    ForAll(x, subtype(x, x)),  # reflexivity
    ForAll([x, y], Implies(extends(x, y), subtype(x, y))),
    ForAll([x, y, z], Implies(And(subtype(x, y), subtype(y, z)), subtype(x, z))),  # transitivity
    ForAll([x, y], Implies(And(subtype(x, y), subtype(y, x)), x == y)),
    ForAll([x, y, z], Implies(And(extends(x, z), extends(y, z), x != y), And(not_subtype(x, y), not_subtype(y, x)))),
    ForAll([x, y, z], Implies(And(subtype(x, y), not_subtype(y, z)), Not(subtype(x, z)))),
]

generics_axioms = [
    ForAll([x, y], Implies(subtype(x, List(y)), y == list_type(x))),
    ForAll([x, y], Implies(subtype(x, Set(y)), y == set_type(x))),
    ForAll([x, y, z], Implies(subtype(x, Dict(y, z)), And(y == dict_key_type(x), z == dict_value_type(x))))
]

num_strength_properties = [
    ForAll(x, Implies(subtype(x, Num), stronger_num(x, x))),
    ForAll([x, y, z], Implies(And(stronger_num(x, y), stronger_num(y, z)), stronger_num(x, z))),
    ForAll([x, y], Implies(And(stronger_num(x, y), x != y), Not(stronger_num(y, x)))),
    ForAll([x, y], Implies(Not(And(subtype(x, Num), subtype(y, Num))),
                           Not(Or(stronger_num(x, y), stronger_num(y, x)))))
]

axioms = [
    extends(zNone, Object),
    extends(Num, Object),
    extends(Complex, Num),
    extends(Float, Num),
    extends(Int, Num),
    extends(Bool, Int),
    extends(Seq, Object),
    extends(String, Seq),
    extends(Bytes, Seq),
    extends(Tuple, Seq),

    ForAll([x], extends(Tuple1(x), Tuple), patterns=[Tuple1(x)]),
    ForAll([x, y], extends(Tuple2(x, y), Tuple), patterns=[Tuple2(x, y)]),
    ForAll([x, y, z], extends(Tuple3(x, y, z), Tuple), patterns=[Tuple3(x, y, z)]),
    ForAll([x, y, z, l], extends(Tuple4(x, y, z, l), Tuple), patterns=[Tuple4(x, y, z, l)]),
    ForAll([x, y, z, l, m], extends(Tuple5(x, y, z, l, m), Tuple), patterns=[Tuple5(x, y, z, l, m)]),

    extends(Func, Object),
    ForAll([x], extends(Func0(x), Func), patterns=[Func0(x)]),
    ForAll([x, y], extends(Func1(x, y), Func), patterns=[Func1(x, y)]),
    ForAll([x, y, z], extends(Func2(x, y, z), Func), patterns=[Func2(x, y, z)]),
    ForAll([x, y, z, l], extends(Func3(x, y, z, l), Func), patterns=[Func3(x, y, z, l)]),
    ForAll([x, y, z, l, m], extends(Func4(x, y, z, l, m), Func), patterns=[Func4(x, y, z, l, m)]),
    ForAll([x, y, z, l, m, n], extends(Func5(x, y, z, l, m, n), Func), patterns=[Func5(x, y, z, l, m, n)]),

    ForAll([x], extends(List(x), Seq), patterns=[List(x)]),
    ForAll([x], extends(Set(x), Object), patterns=[Set(x)]),
    ForAll([x, y], extends(Dict(x, y), Object), patterns=[Dict(x, y)]),

    stronger_num(Int, Bool),
    stronger_num(Float, Int),
    stronger_num(Complex, Float),
    stronger_num(Num, Complex)
    ]


# Unique id given to newly created Z3 consts
_element_id = 0


def new_element_id():
    global _element_id
    _element_id += 1
    return _element_id


def new_z3_const(name):
    return Const("{}_{}".format(name, new_element_id()), type_sort)


class TypesSolver(Solver):
    """Z3 solver that has all the type system axioms initialized."""
    def __init__(self, solver=None, ctx=None):
        super().__init__(solver, ctx)
        self.set(auto_config=False, mbqi=False)
        self.init_axioms()

    def init_axioms(self):
        self.add(subtype_properties + axioms + num_strength_properties + generics_axioms)


solver = TypesSolver()  # The main solver for the python program
