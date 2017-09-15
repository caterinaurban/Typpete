"""The type-system for Python 3 encoded in Z3.

Limitations:
    - Multiple inheritance is not supported.
    - Functions with generic type variables are not supported.
"""
from collections import OrderedDict
from frontend.annotation_resolver import AnnotationResolver
from frontend.class_node import ClassNode
from frontend.config import config
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
# set_param("timeout", 1000 * 300)
# set_option(":smt.qi.profile", True)
# set_param(verbose=10)


class TypesSolver(Solver):
    """Z3 solver that has all the type system axioms initialized."""

    def __init__(self, tree, solver=None, ctx=None):
        super().__init__(solver, ctx)
        # self.set(auto_config=False, mbqi=False, unsat_core=True)
        self.set(auto_config=False, mbqi=False, unsat_core=True)
        self.element_id = 0     # unique id given to newly created Z3 consts
        self.assertions_vars = []
        self.assertions_errors = {}
        self.stubs_handler = StubsHandler()
        analyzer = PreAnalyzer(tree, ["/home/marco/infer_scion_types/scion/scion-stubs", "/home/marco/infer_scion_types/scion/stubs"], self.stubs_handler)     # TODO: avoid hard-coding
        self.config = analyzer.get_all_configurations()
        self.z3_types = Z3Types(self.config)
        self.annotation_resolver = AnnotationResolver(self.z3_types)
        self.optimize = Optimize(ctx)
        # self.optimize.set("timeout", 30000)
        self.all_assertions = []
        self.init_axioms()

    def add(self, *args, fail_message, force=False):
        assertion = self.new_z3_const("assertion_bool", BoolSort())
        self.assertions_vars.append(assertion)
        self.assertions_errors[assertion] = fail_message
        self.optimize.add(*args)
        implication = Implies(assertion, And(*args))
        super().add(implication)
        self.all_assertions.append(implication)
        if force:
            self.all_assertions.append(And(*args))

    def init_axioms(self):
        self.add(self.z3_types.subtyping, fail_message="Subtyping error", force=True)

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
        self.class_to_funcs = config.class_to_funcs

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
        self.complex = type_sort.complex
        self.float = type_sort.float
        self.int = type_sort.int
        self.bool = type_sort.bool
        # sequences
        self.seq = type_sort.sequence
        self.string = type_sort.str
        self.str = type_sort.str
        self.bytes = type_sort.bytes
        self.tuple_var = type_sort.tuple_var
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

        # function representing subtyping between types: subtype(x, y) if and only if x is a subtype of y
        self.subtype = Function("subtype", type_sort, type_sort, BoolSort())
        self.subtyping = self.create_subtype_axioms(config.all_classes, type_sort)

    def create_class_tree(self, all_classes, type_sort):
        """
        Creates a tree consisting of ClassNodes which contains all classes in all_classes,
        where child nodes are subclasses. The root will be object.
        """
        graph = ClassNode('object', [], type_sort)
        to_cover = list(self.config.builtins.keys()) + list(self.config.others.keys())
        covered_again = []
        covered = {'object'}
        i = 0
        while i < len(to_cover):
            current = to_cover[i]
            i += 1
            bases = all_classes[current]
            cont = False
            for base in bases:
                if base not in covered:
                    cont = True
                    break
            if cont:
                to_cover.append(current)
                covered_again.append(current)
                continue

            current_node = ClassNode(current, [], type_sort)
            for base in bases:
                base_node = graph.find(base)
                current_node.parents.append(base_node)
                base_node.children.append(current_node)
            covered.add(current)
        return graph

    def create_subtype_axioms(self, all_classes, type_sort):
        """
        Creates axioms defining subtype relations for all possible classes.
        """
        tree = self.create_class_tree(all_classes, type_sort)
        axioms = []
        # For each class C in the program, create two axioms:
        for c in tree.all_children():
            c_literal = c.get_literal()
            x = Const("x", self.type_sort)
            is_tuple_var = str(c_literal).startswith('tuple_var')
            is_tuple_n = str(c_literal).startswith('tuple') and not str(c_literal).startswith('tuple_var')

            # One which is triggered by subtype(C, X)
            if c.name != 'none' or not config["none_subtype_of_all"]:
                options = []
                if is_tuple_n:
                    for base in c.all_parents():
                        if base.name == ('tuple_var', 'tuple_type'):
                            arg_subtypes = []
                            for arg in c.quantified():
                                arg_subtypes.append(self.subtype(arg, base.get_arg_list(x)[0]))
                            _res = And(x == base.get_literal_with_args(x), *arg_subtypes)
                            options.append(_res)
                        else:
                            options.append(x == base.get_literal())
                else:
                    for base in c.all_parents():
                        options.append(x == base.get_literal())
                subtype_expr = self.subtype(c_literal, x)
                axiom = ForAll([x] + c.quantified(), subtype_expr == Or(*options),
                               patterns=[subtype_expr])
                axioms.append(axiom)

            # And one which is triggered by subtype(X, C)
            options = [x == type_sort.none] if config["none_subtype_of_all"] else []
            if is_tuple_var:
                for sub in c.all_children():
                    if sub is c:
                        options.append(x == c_literal)
                    else:
                        arg_subtypes = []
                        for arg in sub.get_arg_list(x):
                            arg_subtypes.append(
                                self.subtype(arg, c.quantified()[0]))
                        _res = And(x == sub.get_literal_with_args(x), *arg_subtypes)
                        options.append(_res)
            else:
                for sub in c.all_children():
                    if sub is c:
                        options.append(x == c_literal)
                    else:
                        options.append(x == sub.get_literal_with_args(x))
            # # One which is triggered by subtype(C, X)
            # # Check whether to make non subtype of everything or not
            # if c.name != 'none' or c.name == 'none' and not config["none_subtype_of_all"]:
            #     # Handle tuples and functions variance
            #     if isinstance(c.name, tuple) and (c.name[0].startswith("tuple") or c.name[0].startswith("func")):
            #         # Get the accessors of X
            #         accessors = []
            #         for acc_name in c.name[1:]:
            #             accessors.append(getattr(type_sort, acc_name)(x))
            #
            #         # Add subtype relationship between args of X and C
            #         args_sub = []
            #         consts = c.quantified()
            #
            #         if c.name[0].startswith("tuple"):
            #             for i, accessor in enumerate(accessors):
            #                 args_sub.append(self.subtype(consts[i], accessor))
            #         else:
            #             for i, accessor in enumerate(accessors[1:-1]):
            #                 args_sub.append(self.subtype(accessor, consts[i + 1]))
            #             args_sub.append(self.subtype(consts[-1], accessors[-1]))
            #
            #         options = [
            #             And(x == getattr(type_sort, c.name[0])(*accessors), *args_sub)
            #         ]
            #     else:
            #         options = []
            #     for base in c.all_parents():
            #         options.append(x == base.get_literal())
            #     subtype_expr = self.subtype(c_literal, x)
            #     axiom = ForAll([x] + c.quantified(), subtype_expr == Or(*options),
            #                    patterns=[subtype_expr])
            #     axioms.append(axiom)
            #
            # # And one which is triggered by subtype(X, C)
            # options = [x == type_sort.none] if config["none_subtype_of_all"] else []
            # if isinstance(c.name, tuple) and (c.name[0].startswith("tuple") or c.name[0].startswith("func")):
            #     # Handle tuples and functions variance as above
            #     accessors = []
            #     for acc_name in c.name[1:]:
            #         accessors.append(getattr(type_sort, acc_name)(x))
            #
            #     args_sub = []
            #     consts = c.quantified()
            #
            #     if c.name[0].startswith("tuple"):
            #         for i, accessor in enumerate(accessors):
            #             args_sub.append(self.subtype(accessor, consts[i]))
            #     else:
            #         for i, accessor in enumerate(accessors[1:-1]):
            #             args_sub.append(self.subtype(consts[i + 1], accessor))
            #         args_sub.append(self.subtype(accessors[-1], consts[-1]))
            #
            #     options.append(And(x == getattr(type_sort, c.name[0])(*accessors), *args_sub))
            #
            # for sub in c.all_children():
            #     if sub is c:
            #         options.append(x == c_literal)
            #     else:
            #         options.append(x == sub.get_literal_with_args(x))
            subtype_expr = self.subtype(x, c_literal)
            axiom = ForAll([x] + c.quantified(), subtype_expr == Or(*options),
                           patterns=[subtype_expr])
            axioms.append(axiom)
        return axioms


def declare_type_sort(max_tuple_length, max_function_args, classes_to_instance_attrs):
    """Declare the type data type and all its constructors and accessors."""
    type_sort = Datatype("Type")

    # type constructors and accessors
    type_sort.declare("object")
    type_sort.declare("type", ("instance", type_sort))
    type_sort.declare("none")
    # number
    type_sort.declare("complex")
    type_sort.declare("float")
    type_sort.declare("int")
    type_sort.declare("bool")
    # sequences
    type_sort.declare("sequence")
    type_sort.declare("str")
    type_sort.declare("bytes")
    type_sort.declare("tuple")
    type_sort.declare("tuple_var", ("tuple_type", type_sort))
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
