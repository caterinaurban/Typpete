"""The type-system for Python 3 encoded in Z3.

Limitations:
    - Multiple inheritance is not supported.
    - Functions with generic type variables are not supported.
"""
from collections import OrderedDict
from frontend.annotation_resolver import AnnotationResolver
from frontend.class_node import ClassNode
from frontend.config import config
from frontend.constants import ALIASES
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

    def __init__(self, tree, solver=None, ctx=None, base_folder=''):
        super().__init__(solver, ctx)
        self.set(auto_config=False, mbqi=False, unsat_core=True)
        self.element_id = 0     # unique id given to newly created Z3 consts
        self.assertions_vars = []
        self.assertions_errors = {}
        self.stubs_handler = StubsHandler()
        analyzer = PreAnalyzer(tree, base_folder, self.stubs_handler)
        self.config = analyzer.get_all_configurations()
        self.z3_types = Z3Types(self.config, self)

        # for cls in self.z3_types.classes:
        #     self.z3_types.all_types[cls] = self.z3_types.type(self.z3_types.classes[cls])

        self.annotation_resolver = AnnotationResolver(self.z3_types)
        self.optimize = Optimize(ctx)
        # self.optimize.set("timeout", 30000)
        self.all_assertions = []
        self.forced = set()
        self.init_axioms()

    def add(self, *args, fail_message):
        assertion = self.new_z3_const("assertion_bool", BoolSort())
        self.assertions_vars.append(assertion)
        self.assertions_errors[assertion] = fail_message
        self.optimize.add(*args)
        to_add = Implies(assertion, And(*args))
        super().add(to_add)
        self.all_assertions.append(to_add)

    def init_axioms(self):
        for st in self.z3_types.subtyping:
            self.add(st, fail_message="Subtyping error")
        self.add(self.z3_types.subst_axioms, fail_message="Subst definition")

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

    def resolve_annotation(self, annotation, module):
        return self.annotation_resolver.resolve(annotation, self, module)

    # def create_type_var_axioms(self):
    #     axioms = []
    #     type_var_map = {}
    #     for name, (id, options, bound) in self.config.type_vars.items():
    #         type_var_type = getattr(self.z3_types.type_sort, 'tv' + id)
    #         if options[1:]:
    #             type_options = [self.resolve_annotation(o, type_var_map=type_var_map) for o in options[1:]]
    #             axioms.append(Or(*[self.z3_types.upper(type_var_type) == o for o in type_options]))
    #         else:
    #             if bound:
    #                 bound_type = self.resolve_annotation(bound[0].value, type_var_map=type_var_map)
    #             else:
    #                 bound_type = self.z3_types.object
    #             axioms.append(self.z3_types.upper(type_var_type) == bound_type)
    #         type_var_map[name] = type_var_type
    #     self.add(axioms, fail_message="Type var upper bounds")


class Z3Types:
    def __init__(self, config, solver):
        self.config = config
        self.all_types = OrderedDict()
        self.instance_attributes = OrderedDict()
        self.class_attributes = OrderedDict()
        self.class_to_funcs = config.class_to_funcs

        self.new_z3_const = solver.new_z3_const

        max_tuple_length = config.max_tuple_length
        max_function_args = config.max_function_args
        classes_to_instance_attrs = config.classes_to_instance_attrs
        classes_to_class_attrs = config.classes_to_class_attrs
        class_to_base = config.class_to_base

        type_sort = declare_type_sort(max_tuple_length, max_function_args,
                                      class_to_base, config.type_vars)

        for key, tv_name in config.type_vars.items():
            config.type_vars[key] = getattr(type_sort, "tv" + tv_name)

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
        self.bytes = type_sort.bytes
        self.tuple = type_sort.tuple
        self.tuples = list()
        for cur_len in range(max_tuple_length + 1):
            self.tuples.append(getattr(type_sort, "tuple_{}".format(cur_len)))
        self.list = type_sort.list
        self.list_type = type_sort.list_arg_0
        # sets
        self.set = type_sort.set
        self.set_type = type_sort.set_arg_0
        # dictionaries
        self.dict = type_sort.dict
        self.dict_key_type = type_sort.dict_arg_0
        self.dict_value_type = type_sort.dict_arg_1
        # functions
        self.funcs = list()
        for cur_len in range(max_function_args + 1):
            self.funcs.append(getattr(type_sort, "func_{}".format(cur_len)))
        # classes
        self.classes = OrderedDict()
        for cls in classes_to_instance_attrs:
            key = "class_{}".format(cls) if cls not in ALIASES else ALIASES[cls]
            self.classes[cls] = getattr(type_sort, key)
        create_classes_attributes(type_sort, classes_to_instance_attrs, self.instance_attributes)
        create_classes_attributes(type_sort, classes_to_class_attrs, self.class_attributes)

        method_sort = Datatype("Method")
        method_sort.declare('m__none')

        self.tvs = set()
        self.method_ids = {}
        self.tv_to_method = {}
        for m, vrs in config.type_params.items():
            method_sort.declare('m__' + m)
            for v in vrs:
                tv = getattr(type_sort, 'tv' + str(v))
                self.tvs.add(tv)
                setattr(self, 'tv' + str(v), tv)

        # iterate once before to remove all unused classes/functions
        classes_to_remove = set()
        for c, vrs in config.class_type_params.items():
            if not hasattr(type_sort, "tv" + str(vrs[0])):
                classes_to_remove.add(c)

        for c in classes_to_remove:
            del config.class_type_params[c]

        funcs_to_remove = set()
        for f, vrs in config.type_params.items():
            if not hasattr(type_sort, "tv" + str(vrs[0])):
                funcs_to_remove.add(f)

        for f in funcs_to_remove:
            del config.type_params[f]

        for c, vrs in config.class_type_params.items():
            for v in vrs:
                tv = getattr(type_sort, 'tv' + str(v))
                self.tvs.add(tv)
                setattr(self, 'tv' + str(v), tv)
            for func in config.class_to_funcs[c]:
                name = 'm__' + func
                method_sort.declare(name)


        method_sort = method_sort.create()
        self.method_sort = method_sort
        for m, vrs in config.type_params.items():
            method_id = getattr(method_sort, 'm__' + m)
            self.method_ids[m] = method_id
            for v in vrs:
                tv = getattr(type_sort, 'tv' + str(v))
                self.tv_to_method[tv] = [method_id]

        for c, vrs in config.class_type_params.items():
            for m in config.class_to_funcs[c]:
                method_id = getattr(method_sort, 'm__' + m)
                self.method_ids[c + '.' + m] = method_id
                for v in vrs:
                    tv = getattr(type_sort, 'tv' + str(v))
                    if tv in self.tv_to_method:
                        self.tv_to_method[tv].append(method_id)
                    else:
                        self.tv_to_method[tv] = [method_id]


        self.generics = [type_sort.generic1, type_sort.generic2, type_sort.generic3]
        self.generic1_tv1 = type_sort.generic1_tv1
        self.generic1_func = type_sort.generic1_func
        self.generic2_tv1 = type_sort.generic2_tv1
        self.generic2_tv2 = type_sort.generic2_tv2
        self.generic2_func = type_sort.generic2_func
        self.generic3_tv1 = type_sort.generic3_tv1
        self.generic3_tv2 = type_sort.generic3_tv2
        self.generic3_tv3 = type_sort.generic3_tv3
        self.generic3_func = type_sort.generic3_func
        self.issubst = Function('issubst', type_sort, type_sort, type_sort, type_sort, BoolSort())
        self.subst = Function('subst', type_sort, type_sort, type_sort, type_sort)
        self.upper = Function('upper', type_sort, type_sort)

        # function representing subtyping between types: subtype(x, y) if and only if x is a subtype of y
        self._subtype = Function("subtype", method_sort, type_sort, type_sort, BoolSort())
        self.current_method = method_sort.m__none
        tree = self.create_class_tree(config.all_classes, type_sort)
        self.subtyping = self.create_subtype_axioms(tree)
        self.subst_axioms = self.create_subst_axioms(tree)



    def subtype(self, t0, t1):
        res = self._subtype(self.current_method, t0, t1)
        return res



    @staticmethod
    def create_class_tree(all_classes, type_sort):
        """
        Creates a tree consisting of ClassNodes which contains all classes in all_classes,
        where child nodes are subclasses. The root will be object.
        """
        graph = ClassNode('object', [], type_sort)
        to_cover = list(all_classes.keys())
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
                continue

            current_node = ClassNode(current, [], type_sort)
            for base in bases:
                base_node = graph.find(base)
                current_node.parents.append(base_node)
                base_node.children.append(current_node)
            covered.add(current)
        return graph

    def create_subst_axioms(self, tree):
        axioms = []
        what = self.new_z3_const('what', self.type_sort)
        by = self.new_z3_const('by', self.type_sort)
        in_ = self.new_z3_const('in', self.type_sort)
        is_ = self.new_z3_const('is', self.type_sort)
        for c in tree.all_children():
            literal = c.get_literal()
            is_literal = c.get_literal_with_args(is_)
            args_subst = [self.issubst(arg, what, by, is_arg) if isinstance(arg,
                                                                            DatatypeRef) else arg == is_arg
                          for (is_arg, arg) in
                          zip(c.get_quantified_with_args(is_), c.quantified())]
            axiom = ForAll([what, by, is_] + c.quantified(),
                           self.issubst(literal, what, by, is_) == Or(
                               And(is_ == by, literal == what),
                               And(what != literal, is_ == is_literal, *args_subst)),
                           patterns=[self.issubst(literal, what, by, is_)])
            axioms.append(axiom)

            in_literal = c.get_literal_with_args(in_)
            args_subst = [self.issubst(in_arg, what, by, arg) if isinstance(arg,
                                                                            DatatypeRef) else arg == in_arg
                          for (in_arg, arg) in
                          zip(c.get_quantified_with_args(in_), c.quantified())]
            axiom = ForAll([what, by, in_] + c.quantified(),
                           self.issubst(in_, what, by, literal) == Or(
                               And(by == literal, what == in_),
                               And(what != in_, in_ == in_literal, *args_subst)),
                           patterns=[self.issubst(in_, what, by, literal)])
            axioms.append(axiom)
        subst_def = ForAll([in_, what, by],
                           self.issubst(in_, what, by, self.subst(in_, what, by)),
                           patterns=[self.subst(in_, what, by)])
        axioms.append(subst_def)
        for i in range(3):
            args = []
            for j in range(i + 1):
                args.append(self.new_z3_const('v' + str(j + 1), self.type_sort))
            func = self.generics[i]
            normal_func = self.new_z3_const('normal_func', self.type_sort)
            literal = func(*args, normal_func)
            axiom = ForAll([what, by, normal_func] + args,
                           self.subst(literal, what, by) == literal,
                           patterns=[self.subst(literal, what, by)])
            axioms.append(axiom)

        for tv in self.tvs:
            axiom = ForAll([what, by, is_], self.issubst(tv, what, by, is_) == Or(And(tv == what, by == is_), And(tv != what, tv == is_)),
                           patterns=[self.issubst(tv, what, by, is_)])
            axioms.append(axiom)
            axiom = ForAll([what, by, in_], self.issubst(in_, what, by, tv) == Or(
                And(in_ == what, by == tv), And(in_ != what, tv == in_)),
                           patterns=[self.issubst(in_, what, by, tv)])
            axioms.append(axiom)

        return axioms

    def create_subtype_axioms(self, tree):
        """
        Creates axioms defining subtype relations for all possible classes.
        """
        axioms = []
        x = self.new_z3_const("x", self.type_sort)
        m = self.new_z3_const('m', self.method_sort)
        # For each class C in the program, create two axioms:
        for c in tree.all_children():
            c_literal = c.get_literal()
            # One which is triggered by subtype(C, X)
            # Check whether to make non subtype of everything or not
            if c.name != 'none' or c.name == 'none' and not config["none_subtype_of_all"]:
                # Handle tuples and functions variance
                if isinstance(c.name, tuple) and (c.name[0].startswith("tuple") or c.name[0].startswith("func")):
                    # Get the accessors of X
                    accessors = []
                    for acc_name in c.name[1:]:
                        accessors.append(getattr(self.type_sort, acc_name)(x))

                    # Add subtype relationship between args of X and C
                    args_sub = []
                    consts = c.quantified()

                    if c.name[0].startswith("tuple"):
                        for i, accessor in enumerate(accessors):
                            args_sub.append(self.subtype(consts[i], accessor))
                    else:
                        for i, accessor in enumerate(accessors[1:-1]):
                            args_sub.append(self.subtype(accessor, consts[i + 1]))
                        args_sub.append(self.subtype(consts[-1], accessors[-1]))

                    options = [
                        And(x == getattr(self.type_sort, c.name[0])(*accessors), *args_sub)
                    ]
                else:
                    options = []
                for base in c.all_parents():
                    options.append(x == base.get_literal())
                subtype_expr = self._subtype(m, c_literal, x)
                axiom = ForAll([x, m] + c.quantified(), subtype_expr == Or(*options),
                               patterns=[subtype_expr])
                axioms.append(axiom)

            # And one which is triggered by subtype(X, C)
            options = [x == self.type_sort.none] if config["none_subtype_of_all"] else []
            if isinstance(c.name, tuple) and (c.name[0].startswith("tuple") or c.name[0].startswith("func")):
                # Handle tuples and functions variance as above
                accessors = []
                for acc_name in c.name[1:]:
                    accessors.append(getattr(self.type_sort, acc_name)(x))

                args_sub = []
                consts = c.quantified()

                if c.name[0].startswith("tuple"):
                    for i, accessor in enumerate(accessors):
                        args_sub.append(self.subtype(accessor, consts[i]))
                else:
                    for i, accessor in enumerate(accessors[1:-1]):
                        args_sub.append(self.subtype(consts[i + 1], accessor))
                    args_sub.append(self.subtype(accessors[-1], consts[-1]))

                options.append(And(x == getattr(self.type_sort, c.name[0])(*accessors), *args_sub))

            for sub in c.all_children():
                if sub is c:
                    options.append(x == c_literal)
                else:
                    options.append(x == sub.get_literal_with_args(x))
            for tv in self.tvs:
                option = And(Or(*[m == m_tv for m_tv in self.tv_to_method[tv]]), x == tv, self._subtype(m, self.upper(tv), c_literal))
                options.append(option)
            subtype_expr = self._subtype(m, x, c_literal)
            axiom = ForAll([x, m] + c.quantified(), subtype_expr == Or(*options),
                           patterns=[subtype_expr])
            axioms.append(axiom)

        for tv in self.tvs:
            options = [x == tv, x == self.none]
            for tvp in self.tvs:
                if tvp is tv:
                    continue
                intersect = set(self.tv_to_method[tv]).intersection(set(self.tv_to_method[tvp]))
                if not intersect:
                    continue
                options.append(And(Or(*[m == tvm for tvm in intersect]), x == tvp, self.upper(tvp) == tv))
            axiom = ForAll([x, m], self._subtype(m, x, tv) == Or(*options),
                           patterns = [self._subtype(m, x, tv)])
            axioms.append(axiom)
            axiom = ForAll([x, m], self._subtype(m, tv, x) == Or(x == tv,
                                                                 And(Or(*[m == m_tv for m_tv in self.tv_to_method[tv]]),
                                                                     self._subtype(m, self.upper(tv), x))),
                           patterns = [self._subtype(m, tv, x)])
            axioms.append(axiom)

        for i in range(3):
            args = []
            for j in range(i + 1):
                args.append(self.new_z3_const('v' + str(j + 1), self.type_sort))
            func = self.generics[i]
            normal_func = self.new_z3_const('normal_func', self.type_sort)
            literal = func(*args, normal_func)
            axiom = ForAll([x, m] + args + [normal_func], self._subtype(m, literal, x) == ( x == literal),
                           patterns = [self._subtype(m, literal, x)])
            axioms.append(axiom)
            axiom = ForAll([x, m] + args + [normal_func], self._subtype(m, x, literal) == (x == literal),
                           patterns = [self._subtype(m, x, literal)])
            axioms.append(axiom)
        return axioms


def declare_type_sort(max_tuple_length, max_function_args, classes_to_base, type_vars):
    """Declare the type data type and all its constructors and accessors."""
    type_sort = Datatype("Type")

    # type constructors and accessors
    type_sort.declare("object")
    type_sort.declare("type", ("type_arg_0", type_sort))
    type_sort.declare("none")
    # number
    type_sort.declare("complex")
    type_sort.declare("float")
    type_sort.declare("int")
    type_sort.declare("bool")

    for tp in type_vars.values():
        type_sort.declare("tv" + tp)

    # for cls, vrs in type_params.items():
    #     for v in vrs:
    #         type_sort.declare('tv' + str(v))
    # for cls, vrs in class_type_params.items():
    #     for v in vrs:
    #         type_sort.declare('tv' + str(v))
    type_sort.declare('generic1', ('generic1_tv1', type_sort), ('generic1_func', type_sort))
    type_sort.declare('generic2', ('generic2_tv1', type_sort), ('generic2_tv2', type_sort), ('generic2_func', type_sort))
    type_sort.declare('generic3', ('generic3_tv1', type_sort), ('generic3_tv2', type_sort), ('generic3_tv3', type_sort), ('generic3_func', type_sort))

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
    type_sort.declare("list", ("list_arg_0", type_sort))
    # sets
    type_sort.declare("set", ("set_arg_0", type_sort))
    # dictionaries
    type_sort.declare("dict", ("dict_arg_0", type_sort), ("dict_arg_1", type_sort))
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
    for cls in classes_to_base:
        if isinstance(cls, str):
            if cls in ALIASES:
                continue
            type_sort.declare("class_{}".format(cls))
        else:
            if cls[0] in ALIASES:
                continue
            type_sort.declare("class_{}".format(cls[0]), *[(a, type_sort) for a in cls[1:]])

    return type_sort.create()


def create_classes_attributes(type_sort, classes_to_attrs, attributes_map):
    for cls in classes_to_attrs:
        attrs = classes_to_attrs[cls]
        attributes_map[cls] = OrderedDict()
        for attr in attrs:
            attribute = Const("class_{}_attr_{}".format(cls, attr), type_sort)
            attributes_map[cls][attr] = attribute
