"""The type-system for Python 3 encoded in Z3.

Limitations:
    - Multiple inheritance is not supported.
    - Functions with generic type variables are not supported.
"""
from z3 import *


def declare_type_sort(max_tuple_length, max_function_args):
    """Declare the type Z3 data-type and all its constructors/accessors"""
    type_sort = Datatype("Type")

    # Declare constructors
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

    # Create dynamic tuple length constructors, based on the configurations given by the pre-analysis
    type_sort.declare("tuple")

    # Create tuples from zero length to max length
    for cur_len in range(max_tuple_length + 1):
        # Create tuple elements accessors
        accessors = []
        for arg in range(cur_len):
            accessor = ("tuple_{}_arg_{}".format(cur_len, arg + 1), type_sort)
            accessors.append(accessor)

        type_sort.declare("tuple_{}".format(cur_len), *accessors)

    # Create dynamic function args length constructors, based on the configurations given by the pre-analysis
    type_sort.declare("func")

    for cur_len in range(max_function_args + 1):
        accessors = []
        # Create arguments accessors
        for arg in range(cur_len):
            accessor = ("func_{}_arg_{}".format(cur_len, arg + 1), type_sort)
            accessors.append(accessor)

        # Create return type accessor
        accessors.append(("func_{}_return".format(cur_len), type_sort))

        type_sort.declare("func_{}".format(cur_len), *accessors)

    type_sort = type_sort.create()
    return type_sort


def get_tuples(type_sort, max_tuple_length):
    """Extract the tuples constructors from the type_sort data-type"""
    tuples = []
    for cur_len in range(max_tuple_length + 1):
        tuples.append(getattr(type_sort, "tuple_{}".format(cur_len)))
    return tuples


def get_funcs(type_sort, max_function_args):
    """Extract the functions constructors from the type_sort data-type"""
    funcs = []
    for cur_len in range(max_function_args + 1):
        funcs.append(getattr(type_sort, "func_{}".format(cur_len)))
    return funcs


def tuples_subtype_axioms(tuples, type_sort):
    """Add the axioms for the tuples subtyping"""

    # Initialize constants to be used in the ForAll quantifier
    # Each tuple needs a number of quantifiers equal to its length
    # With n tuples, from zero-length to (n - 1) length tuples, we need at most n - 1 quantifiers.
    quantifiers_consts = [Const("tuples_q_{}".format(x), type_sort) for x in range(len(tuples) - 1)]
    axioms = []
    for i in range(len(tuples)):
        # Tuple tuples[i] will have length i
        if i == 0:
            # Zero length tuple: An expression not a call.
            axioms.append(subtype(tuples[i], type_sort.tuple))
        else:
            # Tuple tuples[i] uses exactly i constants
            consts = quantifiers_consts[:i]
            inst = tuples[i](consts)
            axioms.append(
                ForAll(consts, subtype(inst, type_sort.tuple), patterns=[inst])
            )
    return axioms


def functions_subtype_axioms(funcs, type_sort):
    """Add the axioms for the functions subtyping"""

    # Initialize constants to be used in the ForAll quantifier
    # Each function needs a number of quantifiers equal to its args length + 1 (for the return type).
    # With n functions, from zero-length to (n - 1) length arguments, we need at most n quantifiers.
    quantifiers_consts = [Const("funcs_q_{}".format(x), type_sort) for x in range(len(funcs))]
    axioms = []
    for i in range(len(funcs)):
        # function funcs[i] will have i arguments and 1 return type, so  it uses i + 1 constants
        consts = quantifiers_consts[:i + 1]
        inst = funcs[i](consts)
        axioms.append(
            ForAll(consts, subtype(inst, type_sort.func), patterns=[inst])
        )
    return axioms

type_sort = None
Object = zNone = Num = Complex = Float = Int = Bool = Seq = String = Bytes = None
List = list_type = None
Set = set_type = None
Dict = dict_key_type = dict_value_type = None
Tuple = Tuples = None
Func = Funcs = None
subtype = extends = stronger_num = None
subtype_properties = generics_axioms = num_strength_properties = axioms = None
solver = None
x = y = z = None


def init_types(config):
    """Initialize the type system in Z3 using configurations given by the pre-analyzer"""
    max_tuple_length = config["max_tuple_length"]
    max_function_args = config["max_function_args"]

    # Using globals because they are used as module-level variables in other modules
    global type_sort
    global Object, zNone, Num, Complex, Float, Int, Bool, Seq, String, Bytes
    global List, list_type
    global Set, set_type
    global Dict, dict_key_type, dict_value_type
    global Tuple, Tuples
    global Func, Funcs
    global subtype, extends, stronger_num
    global subtype_properties, generics_axioms, num_strength_properties, axioms
    global solver
    global x, y, z

    type_sort = declare_type_sort(max_tuple_length, max_function_args)

    # Extract types constructors
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
    Tuples = get_tuples(type_sort, max_tuple_length)

    Func = type_sort.func
    Funcs = get_funcs(type_sort, max_function_args)

    # Encode subtyping relationships

    subtype = Function("subtype", type_sort, type_sort, BoolSort())
    extends = Function("extends", type_sort, type_sort, BoolSort())
    not_subtype = Function("not subtype", type_sort, type_sort, BoolSort())
    stronger_num = Function("stronger num", type_sort, type_sort, BoolSort())

    x = Const("x", type_sort)
    y = Const("y", type_sort)
    z = Const("z", type_sort)

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

    # For numeric casting purposes:
    # Number > Complex > Float > Int > Bool
    num_strength_properties = [
        ForAll(x, Implies(subtype(x, Num), stronger_num(x, x))),  # Reflexivity
        ForAll([x, y, z], Implies(And(stronger_num(x, y), stronger_num(y, z)), stronger_num(x, z))),  # Transitivity
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

        extends(Func, Object),

        ForAll([x], extends(List(x), Seq), patterns=[List(x)]),
        ForAll([x], extends(Set(x), Object), patterns=[Set(x)]),
        ForAll([x, y], extends(Dict(x, y), Object), patterns=[Dict(x, y)]),

        stronger_num(Int, Bool),
        stronger_num(Float, Int),
        stronger_num(Complex, Float),
        stronger_num(Num, Complex)
        ] + tuples_subtype_axioms(Tuples, type_sort) + functions_subtype_axioms(Funcs, type_sort)

    solver = TypesSolver()

# Unique id given to newly created Z3 consts
_element_id = 0


def new_element_id():
    global _element_id
    _element_id += 1
    return _element_id


def new_z3_const(name):
    """Create a new Z3 constant with a unique name"""
    return Const("{}_{}".format(name, new_element_id()), type_sort)


class TypesSolver(Solver):
    """Z3 solver that has all the type system axioms initialized."""
    def __init__(self, solver=None, ctx=None):
        super().__init__(solver, ctx)
        self.set(auto_config=False, mbqi=False)
        self.init_axioms()

    def init_axioms(self):
        self.add(subtype_properties + axioms + num_strength_properties + generics_axioms)

