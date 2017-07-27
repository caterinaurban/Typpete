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
# set_option(":smt.qi.profile", True)
# set_param(verbose=10)


class TypesSolver(Solver):
    """Z3 solver that has all the type system axioms initialized."""

    def __init__(self, tree, solver=None, ctx=None):
        super().__init__(solver, ctx)
        self.set(auto_config=False, mbqi=False, unsat_core=True)
        self.element_id = 0     # unique id given to newly created Z3 consts
        self.assertions_vars = []
        self.assertions_errors = {}
        self.stubs_handler = StubsHandler()
        analyzer = PreAnalyzer(tree, "tests/inference", self.stubs_handler)     # TODO: avoid hard-coding
        self.config = analyzer.get_all_configurations()
        self.z3_types = Z3Types(self.config)
        self.annotation_resolver = AnnotationResolver(self.z3_types)
        self.optimize = Optimize(ctx)
        # self.optimize.set("timeout", 30000)
        self.init_axioms()

    def add(self, *args, fail_message):
        assertion = self.new_z3_const("assertion_bool", BoolSort())
        self.assertions_vars.append(assertion)
        self.assertions_errors[assertion] = fail_message
        self.optimize.add(*args)
        super().add(Implies(assertion, And(*args)))

    def init_axioms(self):
        self.add(self.z3_types.inheritance + self.z3_types.subtyping, fail_message="Subtyping error")

    def infer_stubs(self, context, infer_func):
        self.stubs_handler.infer_all_files(context, self, self.config.used_names, infer_func)

    def new_element_id(self):
        self.element_id += 1
        return self.element_id

    def new_z3_const(self, name, sort=None):
        """Create a new Z3 constant with a unique name."""
        if sort is None:
            sort = self.z3_types.type_sort
        return Const("{}_{}".format(name, self.new_element_id()), sort)

    def resolve_annotation(self, annotation):
        return self.annotation_resolver.resolve(annotation, self)


class Z3Types:
    def __init__(self, config):
        self.config = config
        self.all_types = OrderedDict()
        self.instance_attributes = OrderedDict()
        self.class_attributes = OrderedDict()
        self.class_to_init_count = config.class_to_init_count

        max_tuple_length = config.max_tuple_length
        max_function_args = config.max_function_args
        classes_to_instance_attrs = config.classes_to_instance_attrs
        classes_to_class_attrs = config.classes_to_class_attrs
        class_to_base = config.class_to_base

        type_sort = declare_type_sort(max_tuple_length, max_function_args, classes_to_instance_attrs)
        self.type_sort = type_sort

        # type constructors and accessors
        self.object = type_sort.object
        self.type = type_sort.type
        self.none = type_sort.none
        # numbers
        self.num = type_sort.number
        self.complex = type_sort.complex
        self.float = type_sort.float
        self.int = type_sort.int
        self.bool = type_sort.bool
        # sequences
        self.seq = type_sort.sequence
        self.string = type_sort.str
        self.bytes = type_sort.bytes
        self.tuple = type_sort.tuple
        self.tuples = list()
        for cur_len in range(max_tuple_length + 1):
            self.tuples.append(getattr(type_sort, "tuple_{}".format(cur_len)))
        self.list = type_sort.list
        self.list_type = type_sort.list_type
        # sets
        self.set = type_sort.set
        self.set_type = type_sort.set_type
        # dictionaries
        self.dict = type_sort.dict
        self.dict_key_type = type_sort.dict_key_type
        self.dict_value_type = type_sort.dict_value_type
        # functions
        self.funcs = list()
        for cur_len in range(max_function_args + 1):
            self.funcs.append(getattr(type_sort, "func_{}".format(cur_len)))
        # classes
        self.classes = OrderedDict()
        for cls in classes_to_instance_attrs:
            self.classes[cls] = getattr(type_sort, "class_{}".format(cls))
        create_classes_attributes(type_sort, classes_to_instance_attrs, self.instance_attributes)
        create_classes_attributes(type_sort, classes_to_class_attrs, self.class_attributes)

        # constants to be used in quantifiers
        x = Const("x", type_sort)
        y = Const("y", type_sort)
        z = Const("z", type_sort)

        # function representing inheritance between types: extends(x, y) if and only if x inherits from y
        self.extends = Function("extends", type_sort, type_sort, BoolSort())
        # function representing subtyping between types: subtype(x, y) if and only if x is a subtype of y
        self.subtype = Function("subtype", type_sort, type_sort, BoolSort())
        # function representing absence of subtyping between types
        self.not_subtype = Function("not subtype", type_sort, type_sort, BoolSort())

        self.inheritance = [
            # types
            ForAll([x], self.extends(self.type(x), self.object), patterns=[self.type(x)], qid="type is obj"),
            # none
            self.extends(self.none, self.object),
            # numbers
            self.extends(self.num, self.object),
            self.extends(self.complex, self.num),
            self.extends(self.float, self.complex),
            self.extends(self.int, self.float),
            self.extends(self.bool, self.int),
            # sequences
            self.extends(self.seq, self.object),
            self.extends(self.string, self.seq),
            self.extends(self.bytes, self.seq),
            self.extends(self.tuple, self.seq),
            ForAll([x], self.extends(self.list(x), self.seq), patterns=[self.list(x)], qid="list is seq"),
            # sets
            ForAll([x], self.extends(self.set(x), self.object), patterns=[self.set(x)], qid="set is obj"),
            # dictionaries
            ForAll([x, y], self.extends(self.dict(x, y), self.object), patterns=[self.dict(x, y)], qid="dict is obj"),
        ]

        self.subtyping = [
            # reflexivity
            ForAll(x, self.subtype(x, x), patterns=[self.subtype(x, x)], qid="reflex"),
            # antisymmetry
            ForAll([x, y], Implies(And(self.subtype(x, y), self.subtype(y, x)), x == y),
                   patterns=[MultiPattern(self.subtype(x, y), self.subtype(y, x))], qid="antisym"),
            # transitivity
            ForAll([x, y, z], Implies(And(self.subtype(x, y), self.subtype(y, z)), self.subtype(x, z)),
                   patterns=[MultiPattern(self.subtype(x, y), self.subtype(y, z))], qid="trans"),

            # inheritance implies subtyping: if x inherits from y, then x is a subtype of y
            #       y
            #     /
            #   x
            ForAll([x, y], Implies(self.extends(x, y), self.subtype(x, y)),
                   patterns=[self.extends(x, y)], qid="extends"),
            # if different types x and y inherit from the same type z, then they cannot be subtypes of each other
            #       z
            #     /   \
            #   x       y
            ForAll([x, y, z], Implies(And(x != y, self.extends(x, z), self.extends(y, z)),
                                      And(self.not_subtype(x, y), self.not_subtype(y, x))),
                   patterns=[MultiPattern(self.extends(x, z), self.extends(y, z))], qid="not_subtype"),
            # if x is a subtype of y and y is not a subtype of z, then x cannot be a subtype of z
            #       o
            #     /   \
            #   z       y
            #             \
            #               x
            ForAll([x, y, z], Implies(And(self.subtype(x, y), self.not_subtype(y, z)),
                                      Not(self.subtype(x, z))),
                   patterns=[MultiPattern(self.subtype(x, y), self.not_subtype(y, z))], qid="not subtype"),

            # a generic type is invariant
            ForAll([x, y], Implies(self.subtype(x, self.type(y)), x == self.type(y)),
                   patterns=[self.subtype(x, self.type(y))], qid="generic type"),
            # a generic list type is invariant
            ForAll([x, y], Implies(self.subtype(x, self.list(y)), x == self.list(y)),
                   patterns=[self.subtype(x, self.list(y))], qid="generic list"),
            # a generic set type is invariant
            ForAll([x, y], Implies(self.subtype(x, self.set(y)), x == self.set(y)),
                   patterns=[self.subtype(x, self.set(y))], qid="generic set"),
            # a generic dictionary type is invariant
            ForAll([x, y, z], Implies(self.subtype(x, self.dict(y, z)), x == self.dict(y, z)),
                   patterns=[self.subtype(x, self.dict(y, z))], qid="generic dict")
        ] + self.tuples_axioms() + self.functions_axioms() + self.classes_axioms(class_to_base)
        self.subtyping = self.create_all_axioms(config.all_classes, type_sort)

    def create_all_axioms(self, all_classes, type_sort):
        class Node:
            def __init__(self, name, parent_node):
                self.name = name
                self.parent_node = parent_node
                self.children = []

            def find(self, name):
                if name == self.name:
                    return self
                for c in self.children:
                    res = c.find(name)
                    if res:
                        return res

            def __str__(self):
                return str(self.name)

            def all(self):
                result = [self]
                for c in self.children:
                    result += c.all()
                return result

            def all_super(self):
                result = [self]
                if self.parent_node:
                    result += self.parent_node.all_super()
                return result

            def get_literal(self):
                if isinstance(self.name, str):
                    return getattr(type_sort, self.name)
                else:
                    constr = getattr(type_sort, self.name[0])
                    args = self.quantified()
                    return constr(*args)

            def get_literal_with_args(self, var):
                if isinstance(self.name, str):
                    return getattr(type_sort, self.name)
                else:
                    constr = getattr(type_sort, self.name[0])
                    args = []
                    for arg in self.name[1:]:
                        args.append(getattr(type_sort, arg)(var))
                    return constr(*args)

            def quantified(self):
                res = []
                if isinstance(self.name, tuple):
                    for i, arg in enumerate(self.name[1:]):
                        sort = type_sort if not arg.endswith('defaults_args') else IntSort()
                        cur = Const("y" + str(i), sort)
                        res.append(cur)
                return res



        tree = Node('object', None)
        to_cover = list(all_classes.keys())
        covered = {'object'}
        i = 0
        while i < len(to_cover):
            current = to_cover[i]
            i += 1
            base = all_classes[current]
            if base not in covered:
                to_cover.append(current)
                continue
            base_node = tree.find(base)
            current_node = Node(current, base_node)
            base_node.children.append(current_node)
            covered.add(current)

            axioms = []
        for c in tree.all():
            c_literal = c.get_literal()
            x = Const("x", self.type_sort)

            # subtype(c, Y)
            options = []
            for sub in c.all_super():
                options.append(x == sub.get_literal())
            subtype_expr = self.subtype(c_literal, x)
            axiom = ForAll([x] + c.quantified(), subtype_expr == Or(*options), patterns=[subtype_expr])
            axioms.append(axiom)

            # subtype(X, c)
            options = []
            for super in c.all():
                options.append(x == super.get_literal_with_args(x))
            subtype_expr = self.subtype(x, c_literal)
            axiom = ForAll([x] + c.quantified(), subtype_expr == Or(*options), patterns=[subtype_expr])
            axioms.append(axiom)
        return axioms


    def tuples_axioms(self):
        """Axioms for tuple subtyping."""
        type_sort = self.type_sort
        tuples = self.tuples

        # constants to be used in quantifiers
        x = Const("x", type_sort)
        # each tuple needs a number of constants equal to its length
        # for n tuples, from zero-length to (n - 1)-length, we need at most n - 1 constants
        consts = [Const("tuples_q_{}".format(x), type_sort) for x in range(len(tuples) - 1)]
#
        axioms = list()
        # zero-length tuple
        axioms.append(self.extends(tuples[0], type_sort.tuple))
        # a generic zero-length tuple type is invariant
        axioms.append(ForAll(x, Implies(self.subtype(x, tuples[0]), x == tuples[0]),
                             patterns=[self.subtype(x, tuples[0])]))
        # i-length tuples
        for i in range(1, len(tuples)):
            quantified = consts[:i]         # tuples[i] uses i constants
            inst = tuples[i](quantified)    # type of tuples[i]
            # tuples[i] inherits from sequence
            axioms.append(ForAll(quantified, self.extends(inst, type_sort.tuple), patterns=[inst]))
            # a generic tuple type is invariant
            axioms.append(ForAll([x] + quantified, Implies(self.subtype(x, inst), x == inst),
                          patterns=[self.subtype(x, inst)]))
        return axioms

    def functions_axioms(self):
        """Axioms for function subtyping."""
        type_sort = self.type_sort
        funcs = self.funcs

        # constants to be used in quantifiers
        x = Const("x", type_sort)
        defaults = Const("defaults", IntSort())
        # each function needs a number of constants equal to the number of its arguments plus one (for the return type)
        # for n functions, with zero to (n - 1) arguments, we need at most n constants
        consts = [Const("funcs_q_{}".format(x), type_sort) for x in range(len(funcs))]

        axioms = list()
        for i in range(len(funcs)):
            quantified = [defaults] + consts[:i + 1]    # funcs[i] uses i+1 constants
            inst = funcs[i](quantified)                 # type of funcs[i]
            # funcs[i] inherits from object
            axioms.append(ForAll(quantified, self.extends(inst, type_sort.object), patterns=[inst]))
            # a generic function type is invariant
            axioms.append(ForAll([x] + quantified, Implies(self.subtype(x, inst), x == inst),
                                 patterns=[self.subtype(x, inst)]))
        return axioms

    def classes_axioms(self, sub_to_base):
        """Axioms for class subtyping."""
        classes = self.classes
        type_sort = self.type_sort
        axioms = []
        for cls in classes:
            base_name = sub_to_base[cls]
            if base_name == "object":   # if the base class is object...
                axioms.append(self.extends(classes[cls], type_sort.object))     # cls inherits from object
            else:
                axioms.append(self.extends(classes[cls], classes[base_name]))   # cls inherits from its base class
        return axioms


def declare_type_sort(max_tuple_length, max_function_args, classes_to_instance_attrs):
    """Declare the type data type and all its constructors and accessors."""
    type_sort = Datatype("Type")

    # type constructors and accessors
    type_sort.declare("object")
    type_sort.declare("type", ("instance", type_sort))
    type_sort.declare("none")
    # number
    type_sort.declare("number")
    type_sort.declare("complex")
    type_sort.declare("float")
    type_sort.declare("int")
    type_sort.declare("bool")
    # sequences
    type_sort.declare("sequence")
    type_sort.declare("str")
    type_sort.declare("bytes")
    type_sort.declare("tuple")
    for cur_len in range(max_tuple_length + 1):     # declare type constructors for tuples up to max length
        accessors = []
        # create accessors for the tuple
        for arg in range(cur_len):
            accessor = ("tuple_{}_arg_{}".format(cur_len, arg + 1), type_sort)
            accessors.append(accessor)
        # declare type constructor for the tuple
        type_sort.declare("tuple_{}".format(cur_len), *accessors)
    type_sort.declare("list", ("list_type", type_sort))
    # sets
    type_sort.declare("set", ("set_type", type_sort))
    # dictionaries
    type_sort.declare("dict", ("dict_key_type", type_sort), ("dict_value_type", type_sort))
    # functions
    for cur_len in range(max_function_args + 1):    # declare type constructors for functions
        # the first accessor of the function is the number of default arguments that the function has
        accessors = [("func_{}_defaults_args".format(cur_len), IntSort())]
        # create accessors for the argument types of the function
        for arg in range(cur_len):
            accessor = ("func_{}_arg_{}".format(cur_len, arg + 1), type_sort)
            accessors.append(accessor)
        # create accessor for the return type of the functio
        accessors.append(("func_{}_return".format(cur_len), type_sort))
        # declare type constructor for the function
        type_sort.declare("func_{}".format(cur_len), *accessors)
    # classes
    for cls in classes_to_instance_attrs:
        type_sort.declare("class_{}".format(cls))

    return type_sort.create()


def create_classes_attributes(type_sort, classes_to_attrs, attributes_map):
    for cls in classes_to_attrs:
        attrs = classes_to_attrs[cls]
        attributes_map[cls] = OrderedDict()
        for attr in attrs:
            attribute = Const("class_{}_attr_{}".format(cls, attr), type_sort)
            attributes_map[cls][attr] = attribute
