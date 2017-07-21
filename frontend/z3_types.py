"""The type-system for Python 3 encoded in Z3.

Limitations:
    - Multiple inheritance is not supported.
    - Functions with generic type variables are not supported.
"""
from collections import OrderedDict
from frontend.annotation_resolver import AnnotationResolver
from frontend.pre_analysis import PreAnalyzer
from frontend.stubs.stubs_handler import StubsHandler

from z3 import *


class Z3Types:
    def __init__(self, config):
        self.config = config
        self.all_types = OrderedDict()
        self.instance_attributes = OrderedDict()
        self.class_attributes = OrderedDict()

        max_tuple_length = config.max_tuple_length
        max_function_args = config.max_function_args
        classes_to_instance_attrs = config.classes_to_instance_attrs
        classes_to_class_attrs = config.classes_to_class_attrs
        class_to_base = config.class_to_base

        type_sort = declare_type_sort(max_tuple_length, max_function_args,
                                      classes_to_instance_attrs, classes_to_class_attrs,
                                      self.instance_attributes, self.class_attributes)
        self.type_sort = type_sort

        # Extract types constructors
        self.type = type_sort.type_type
        self.object = type_sort.object

        self.none = type_sort.none

        self.num = type_sort.number
        self.complex = type_sort.complex
        self.float = type_sort.float
        self.int = type_sort.int
        self.bool = type_sort.bool

        self.seq = type_sort.sequence
        self.string = type_sort.str
        self.bytes = type_sort.bytes
        self.list = type_sort.list
        self.list_type = type_sort.list_type

        self.set = type_sort.set
        self.set_type = type_sort.set_type

        self.dict = type_sort.dict
        self.dict_key_type = type_sort.dict_key_type
        self.dict_value_type = type_sort.dict_value_type

        self.tuple = type_sort.tuple
        self.tuples = get_tuples(type_sort, max_tuple_length)

        self.func = type_sort.func
        self.funcs = get_funcs(type_sort, max_function_args)

        self.classes = get_classes(type_sort, classes_to_instance_attrs)

        # Encode subtyping relationships
        self.subtype = Function("subtype", type_sort, type_sort, BoolSort())
        self.extends = Function("extends", type_sort, type_sort, BoolSort())

        x = Const("x", type_sort)
        y = Const("y", type_sort)
        z = Const("z", type_sort)

        self.subtype_properties = [
            ForAll(x, self.subtype(x, x)),  # reflexivity
            ForAll([x, y], Implies(self.extends(x, y), self.subtype(x, y))),
            ForAll([x, y, z], Implies(And(self.subtype(x, y), self.subtype(y, z)), self.subtype(x, z))),  # transitivity
            ForAll([x, y], Implies(And(self.subtype(x, y), self.subtype(y, x)), x == y)),
            ForAll([x, y, z],
                   Implies(And(self.extends(x, z), self.extends(y, z), x != y),
                           And(Not(self.subtype(x, y)), Not(self.subtype(y, x))))),
        ]

        self.generics_axioms = [
            ForAll([x, y], Implies(self.subtype(x, self.type(y)), x == self.type(y))),
            ForAll([x, y], Implies(self.subtype(x, self.list(y)), x == self.list(y))),
            ForAll([x, y], Implies(self.subtype(x, self.set(y)), x == self.set(y))),
            ForAll([x, y, z], Implies(self.subtype(x, self.dict(y, z)), x == self.dict(y, z)))
        ]

        self.axioms = ([
                      self.extends(self.none, self.object),
                      self.extends(self.num, self.object),
                      self.extends(self.complex, self.num),
                      self.extends(self.float, self.complex),
                      self.extends(self.int, self.float),
                      self.extends(self.bool, self.int),
                      self.extends(self.seq, self.object),
                      self.extends(self.string, self.seq),
                      self.extends(self.bytes, self.seq),
                      self.extends(self.tuple, self.seq),

                      self.extends(self.func, self.object),

                      ForAll([x], self.extends(self.type(x), self.object), patterns=[self.type(x)]),
                      ForAll([x], self.extends(self.list(x), self.seq), patterns=[self.list(x)]),
                      ForAll([x], self.extends(self.set(x), self.object), patterns=[self.set(x)]),
                      ForAll([x, y], self.extends(self.dict(x, y), self.object), patterns=[self.dict(x, y)]),
                  ]
                  + self.tuples_subtype_axioms()
                  + self.functions_subtype_axioms()
                  + self.classes_subtype_axioms(class_to_base))

    def tuples_subtype_axioms(self):
        """Add the axioms for the tuples subtyping"""
        tuples = self.tuples
        type_sort = self.type_sort

        # Initialize constants to be used in the ForAll quantifier
        # Each tuple needs a number of quantifiers equal to its length
        # With n tuples, from zero-length to (n - 1) length tuples, we need at most n - 1 quantifiers.
        quantifiers_consts = [Const("tuples_q_{}".format(x), type_sort) for x in range(len(tuples) - 1)]
        axioms = []
        x = Const("x", type_sort)
        for i in range(len(tuples)):
            # Tuple tuples[i] will have length i
            if i == 0:
                # Zero length tuple: An expression not a call.
                axioms.append(self.extends(tuples[i], self.type_sort.tuple))
                axioms.append(ForAll(x, Implies(self.subtype(x, tuples[i]), x == tuples[i])))
            else:
                # Tuple tuples[i] uses exactly i constants
                consts = quantifiers_consts[:i]
                inst = tuples[i](consts)
                axioms.append(
                    ForAll(consts, self.extends(inst, type_sort.tuple), patterns=[inst])
                )
                axioms.append(ForAll([x] + consts, Implies(self.subtype(x, inst), x == inst)))

        return axioms

    def functions_subtype_axioms(self):
        """Add the axioms for the functions subtyping"""
        funcs = self.funcs
        type_sort = self.type_sort

        # Initialize constants to be used in the ForAll quantifier
        # Each function needs a number of quantifiers equal to its args length + 1 (for the return type).
        # With n functions, from zero-length to (n - 1) length arguments, we need at most n quantifiers.
        quantifiers_consts = [Const("funcs_q_{}".format(x), type_sort) for x in range(len(funcs))]
        axioms = []
        x = Const("x", type_sort)
        defaults_const = Const("defaults_const", IntSort())
        for i in range(len(funcs)):
            # function funcs[i] will have i arguments and 1 return type, so  it uses i + 1 constants
            consts = [defaults_const] + quantifiers_consts[:i + 1]
            inst = funcs[i](consts)
            axioms.append(
                ForAll(consts, self.extends(inst, type_sort.func), patterns=[inst])
            )
            axioms.append(ForAll([x] + consts, Implies(self.subtype(x, inst), x == inst)))
        return axioms

    def classes_subtype_axioms(self, sub_to_base):
        """Add the axioms for the classes subtyping"""
        classes = self.classes
        type_sort = self.type_sort
        axioms = []
        for cls in classes:
            base_name = sub_to_base[cls]
            if base_name == "object":
                axioms.append(self.extends(classes[cls], type_sort.object))
                continue

            base = classes[base_name]
            axioms.append(self.extends(classes[cls], base))

        return axioms


def declare_type_sort(max_tuple_length, max_function_args, classes_to_instance_attrs, classes_to_class_attrs,
                      instance_attributes_map, class_attributes_map):
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

    # The first accessor of the function is the number of default args it has
    for cur_len in range(max_function_args + 1):
        accessors = [("func_{}_defaults_args".format(cur_len), IntSort())]
        # Create arguments accessors
        for arg in range(cur_len):
            accessor = ("func_{}_arg_{}".format(cur_len, arg + 1), type_sort)
            accessors.append(accessor)

        # Create return type accessor
        accessors.append(("func_{}_return".format(cur_len), type_sort))

        type_sort.declare("func_{}".format(cur_len), *accessors)

    type_sort.declare("type_type", ("instance", type_sort))
    declare_classes(type_sort, classes_to_instance_attrs)

    type_sort = type_sort.create()

    create_classes_attributes(type_sort, classes_to_instance_attrs, instance_attributes_map)
    create_classes_attributes(type_sort, classes_to_class_attrs, class_attributes_map)

    return type_sort


def declare_classes(type_sort, classes_to_attrs):
    for cls in classes_to_attrs:
        type_sort.declare("class_{}".format(cls))


def create_classes_attributes(type_sort, classes_to_attrs, attributes_map):
    for cls in classes_to_attrs:
        attrs = classes_to_attrs[cls]

        attributes_map[cls] = OrderedDict()
        for attr in attrs:
            attribute = Const("class_{}_attr_{}".format(cls, attr), type_sort)
            attributes_map[cls][attr] = attribute


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


def get_classes(type_sort, classes_to_attrs):
    """Extract the classes constructors from the type_sort data-type"""
    classes = OrderedDict()
    for cls in classes_to_attrs:
        classes[cls] = getattr(type_sort, "class_{}".format(cls))
    return classes


def invert_dict(d):
    result = OrderedDict()
    for key in d:
        result[d[key]] = key

    return result

set_param("auto-config", False)
set_param("smt.mbqi", False)
set_param("model.v2", True)
set_param("smt.phase_selection", 0)
set_param("smt.restart_strategy", 0)
set_param("smt.restart_factor", 1.5)
set_param("smt.arith.random_initial_value", True)
set_param("smt.case_split", 3)
set_param("smt.delay_units", True)
set_param("smt.delay_units_threshold", 16)
set_param("nnf.sk_hack", True)
set_param("smt.qi.eager_threshold", 100)
set_param("smt.qi.cost",  "(+ weight generation)")
set_param("type_check", True)
set_param("smt.bv.reflect", True)


class TypesSolver(Solver):
    """Z3 solver that has all the type system axioms initialized."""
    def __init__(self, tree, solver=None, ctx=None):
        super().__init__(solver, ctx)

        self.set(auto_config=False, mbqi=False, unsat_core=True)

        self.element_id = 0  # Unique id given to newly created Z3 consts
        self.assertions_vars = []
        self.assertions_errors = {}

        analyzer = PreAnalyzer(tree, "tests/inference")
        self.stubs_handler = StubsHandler(analyzer)

        self.config = analyzer.get_all_configurations()
        self.z3_types = Z3Types(self.config)

        self.annotation_resolver = AnnotationResolver(self.z3_types)
        self.optimize = Optimize(ctx)
        self.optimize.set("timeout", 15000)
        self.init_axioms()

    def init_axioms(self):
        self.add(self.z3_types.subtype_properties + self.z3_types.axioms + self.z3_types.generics_axioms,
                 fail_message="Subtyping error")

    def infer_stubs(self, context, infer_func):
        self.stubs_handler.infer_all_files(context, self, self.config.used_names, infer_func)

    def add(self, *args, fail_message):
        assertion = self.new_z3_const("assertion_bool", BoolSort())
        self.assertions_vars.append(assertion)
        self.assertions_errors[assertion] = fail_message
        self.optimize.add(*args)
        super().add(Implies(assertion, And(*args)))

    def new_element_id(self):
        self.element_id += 1
        return self.element_id

    def new_z3_const(self, name, sort=None):
        """Create a new Z3 constant with a unique name"""
        if sort is None:
            sort = self.z3_types.type_sort
        return Const("{}_{}".format(name, self.new_element_id()), sort)

    def resolve_annotation(self, annotation):
        return self.annotation_resolver.resolve(annotation, self)
