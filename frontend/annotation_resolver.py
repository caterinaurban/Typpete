from z3 import Or, And, simplify
import ast
import re


class AnnotationResolver:
    """Resolver for type annotations in functions"""
    def __init__(self, z3_types):
        self.z3_types = z3_types
        self.primitives = {
            "object": z3_types.object,
            "int": z3_types.int,
            "bool": z3_types.bool,
            "float": z3_types.float,
            "complex": z3_types.complex,
            "str": z3_types.string,
            "bytes": z3_types.bytes,
            "sequence": z3_types.seq,
            "Tuple": z3_types.tuple
        }

        self.z3_type_to_PEP = {
            "none": "None",
            "bool": "bool",
            "int": "int",
            "object": "object",
            "float": "float",
            "complex": "complex",
            "str": "str",
            "bytes": "bytes",
            "number": "number",
            "sequence": "sequence",
            "tuple": "Tuple"
        }

        self.type_var_poss = {}
        self.type_var_super = {}

    def resolve(self, annotation, solver, module, generics_map=None, annotated=False):
        """Resolve the type annotation with the following grammar:
        
        :param annotation: the type annotation to be resolved
        :param solver: the SMT solver for the program
        :param generics_map: Optional map that maps generic types names to their types in a specific function call
                
        t = object | int | bool | float | complex | str | bytes | None
            | List[t]
            | Dict[t, t]
            | Set[t]
            | Type[t]
            | Tuple[t*]
            | Callable[[t*], t]
        """
        if isinstance(annotation, ast.NameConstant) and annotation.value is None:
            return solver.z3_types.none
        if isinstance(annotation, (ast.Name, ast.Str)):
            if isinstance(annotation, ast.Str):
                id = annotation.s
            else:
                id = annotation.id
            if '.' in id:
                id = id[id.rfind(".") + 1:]
            if id in self.primitives:
                return self.primitives[id]
            if id in self.z3_types.all_types:
                return getattr(self.z3_types.type_sort, "class_{}".format(id))


            key = (module, id)
            if generics_map is not None and (annotated or key not in self.z3_types.config.type_vars):
                if id in generics_map:
                    return generics_map[id]

                if id not in self.type_var_poss:
                    raise ValueError("Invalid type annotation {} in line {}".format(id, annotation.lineno))

                result_type = solver.new_z3_const("generic")
                generics_map[id] = result_type
                possible_types = [self.resolve(x, solver, module, generics_map) for x in
                                  self.type_var_poss[id]]

                if possible_types:
                    solver.add(Or([result_type == x for x in possible_types]),
                               fail_message = "Generic type in line {}".format(annotation.lineno))
                return result_type
            
            # Check if it's a generic type var
            if key in self.z3_types.config.type_vars:
                return self.z3_types.config.type_vars[key]
            else:
                raise ValueError(
                    "Invalid type annotation {} in line {}".format(id, annotation.lineno))

            # possible_types = [self.resolve(x, solver, generics_map, available_type_args) for x in self.type_var_poss[id]]
            # if possible_types:
            #     solver.add(Or([result_type == x for x in possible_types]),
            #                fail_message="Generic type in line {}".format(annotation.lineno))
            #
            # if id in self.type_var_super:
            #     type_var_super = self.resolve(self.type_var_super[id], solver, generics_map, available_type_args)
            #     solver.add(solver.z3_types.subtype(result_type, type_var_super),
            #                fail_message="Generic bound in line {}".format(annotation.lineno))


        if isinstance(annotation, ast.Subscript):
            if not (isinstance(annotation.value, ast.Name) and isinstance(annotation.slice, ast.Index)):
                raise TypeError("Invalid type annotation in line {}.".format(annotation.lineno))

            annotation_val = annotation.value.id
            if annotation_val == "List":
                # Parse List type
                return self.z3_types.list(self.resolve(annotation.slice.value, solver, module, generics_map=generics_map))
            
            if annotation_val == "Dict":
                # Parse Dict type
                if not (isinstance(annotation.slice.value, ast.Tuple) and len(annotation.slice.value.elts) == 2):
                    raise TypeError("Dict annotation in line {} should have 2 comma-separated args"
                                    .format(annotation.lineno))

                # Get the types of the dict args
                keys_type = self.resolve(annotation.slice.value.elts[0], solver, module, generics_map=generics_map)
                vals_type = self.resolve(annotation.slice.value.elts[1], solver, module, generics_map=generics_map)
                return self.z3_types.dict(keys_type, vals_type)
            
            if annotation_val == "Set":
                # Parse Set type
                return self.z3_types.set(self.resolve(annotation.slice.value, solver, module, generics_map=generics_map))

            if annotation_val == 'Optional':
                return self.resolve(annotation.slice.value, solver, module, generics_map=generics_map)
            
            if annotation_val == "Type":
                # Parse Type type
                return self.z3_types.type(self.resolve(annotation.slice.value, solver, module, generics_map=generics_map))
            
            if annotation_val == "Tuple":
                # Parse Tuple type
                if not isinstance(annotation.slice.value, (ast.Name, ast.Tuple)):
                    raise TypeError("Invalid tuple type annotation in line {}".format(annotation.lineno))

                # Get the types of the tuple args
                if isinstance(annotation.slice.value, ast.Name):
                    tuple_args_types = [self.resolve(annotation.slice.value, solver, module, generics_map=generics_map)]
                else:
                    tuple_args_types = [self.resolve(x, solver, module, generics_map=generics_map) for x in annotation.slice.value.elts]

                if len(tuple_args_types) == 0:
                    return self.z3_types.tuples[0]
                return self.z3_types.tuples[len(tuple_args_types)](*tuple_args_types)
            
            if annotation_val == "Callable":
                # Parse Callable type
                try:
                    assert isinstance(annotation.slice.value, ast.Tuple)
                    assert len(annotation.slice.value.elts) == 2
                    assert isinstance(annotation.slice.value.elts[0], ast.List)
                except AssertionError:
                    raise TypeError("Callable annotation in line {} should be in the format:"
                                    "Callable[[args_types], return_type]".format(annotation.lineno))

                # Get the args and return types
                args_annotations = annotation.slice.value.elts[0].elts
                args_types = [self.resolve(x, solver, module, generics_map=generics_map) for x in args_annotations]
                return_type = self.resolve(annotation.slice.value.elts[1], solver, module, generics_map=generics_map)

                return self.z3_types.funcs[len(args_types)](*([0] + args_types + [return_type]))

            if annotation_val == "Union":
                # Parse Union type
                if not isinstance(annotation.slice.value, (ast.Name, ast.Tuple)):
                    raise TypeError("Invalid union type annotation in line {}".format(annotation.lineno))

                # Get the types of the union args
                if isinstance(annotation.slice.value, ast.Name):
                    union_args_types = [self.resolve(annotation.slice.value, solver, module, generics_map=generics_map)]
                else:
                    union_args_types = [self.resolve(x, solver, module, generics_map=generics_map) for x in annotation.slice.value.elts]

                # The result of the union type is only one of args, Z3 picks the appropriate one
                # according to the added constraints.
                # Therefore, using more than one type from the union in the same program isn't yet supported.
                # For example, the following is not supported:
                # def f(x: Union[int, str]): ...
                # f(1)
                # f("str")
                # TODO add support for above example using union
                result_type = solver.new_z3_const("union")
                solver.add(Or([result_type == arg for arg in union_args_types]),
                           fail_message="Union in type annotation in line {}".format(annotation.lineno))

                return result_type

            if annotation_val in self.z3_types.all_types:
                func = getattr(self.z3_types.type_sort, "class_{}".format(annotation_val))
                if isinstance(annotation.slice.value, ast.Name):
                    args = self.resolve(annotation.slice.value, solver, module, generics_map=generics_map)
                else:
                    args = [self.resolve(x, solver, module, generics_map=generics_map) for x in annotation.slice.value.elts]
                return func(args)
        raise ValueError("Invalid type annotation in line {}".format(annotation.lineno))

    def get_annotated_function_axioms(self, args_types, solver, annotated_function, result_type):

        """Add axioms for a function call to an annotated function
        
        Reprocess the type annotations for every function call to prevent binding a certain type
        to the function definition
        """
        args_annotations = annotated_function.args_annotations
        result_annotation = annotated_function.return_annotation
        defaults_count = annotated_function.defaults_count
        min_args = len(args_annotations) - defaults_count
        max_args = len(args_annotations)
        if len(args_types) < min_args or len(args_types) > max_args:
            return None
        axioms = []
        generics_map = {}

        for i, annotation in enumerate(args_annotations[:len(args_types)]):
            arg_type = self.resolve(annotation, solver, annotated_function.module, generics_map=generics_map, annotated=True)
            axioms.append(args_types[i] == arg_type)
        axioms.append(result_type == self.resolve(result_annotation, solver, annotated_function.module, generics_map, annotated=True))
        return And(axioms)

    def add_type_var(self, target, type_var_node, solver, module):
        if not isinstance(target, ast.Name):
            raise TypeError("TypeVar assignment target should be a variable name.")
        if not type_var_node.args:
            raise TypeError("Invalid type variable declaration in line {}.".format(type_var_node.lineno))
        args = type_var_node.args
        if not isinstance(args[0], ast.Str):
            raise TypeError("Name of type variable in line {} should be a string".format(type_var_node.lineno))
        type_var_name = target.id

        type_var_possibilities = args[1:]
        if module is None or type_var_possibilities:
            if type_var_node.keywords and type_var_node.keywords[0].arg == "bound":
                type_var_super = type_var_node.keywords[0].value
                self.type_var_super[type_var_name] = type_var_super
            self.type_var_poss[type_var_name] = type_var_possibilities
            return

        if not hasattr(solver.z3_types, "tv" + type_var_name):
            return
        type_var_type = getattr(solver.z3_types, "tv" + type_var_name)

        if type_var_node.keywords and type_var_node.keywords[0].arg == "bound":
            bound = self.resolve(type_var_node.keywords[0].value, solver, module)
            solver.add(solver.z3_types.upper(type_var_type) == bound,
                       fail_message="Upper bound of type variable {}".format(type_var_name))
        elif len(type_var_possibilities) > 0:
            if len(type_var_possibilities) == 1:
                raise TypeError("A single constraint is not allowed in TypeVar in line {}".format(type_var_node.lineno))
            possibilities = [solver.z3_types.upper(type_var_type) == self.resolve(p, solver, module)
                             for p in type_var_possibilities]
            solver.add(Or(*possibilities), fail_message="Options of type variable {}".format(type_var_name))
        else:
            bound = solver.z3_types.object
            solver.add(solver.z3_types.upper(type_var_type) == bound,
                       fail_message="Upper bound of type variable {}".format(
                           type_var_name))

    def unparse_annotation(self, z3_type):
        """Unparse the z3_type into a type annotation in PEP 484 syntax
        
        :param z3_type: The z3 type to be unparsed
        :returns str: the unparsed z3_type in PEP 484 syntax
        """
        type_str = str(z3_type)

        if type_str in self.z3_type_to_PEP: # check if normal type
            return self.z3_type_to_PEP[type_str]

        # Use regex to match the prefix of the string representation of z3_type

        match = re.match("list", type_str)
        # unparse list type. Example: list(int) -> List[int]
        if match:
            # get the list elements' type
            list_type_accessor = self.z3_types.list_type
            list_type = simplify(list_type_accessor(z3_type))
            return "List[{}]".format(self.unparse_annotation(list_type))

        match = re.match("class_(.+)", type_str)
        # unparse user defined class types. Example: class_A -> A
        if match:
            generic = re.match("([a-zA-Z]+)\(.+\)", match.group(1))
            if generic:
                generic_name = generic.group(1)
                type_def = None
                for cls in self.z3_types.config.all_classes:
                    if not isinstance(cls, tuple):
                        continue
                    if cls[0] == 'class_' + generic_name:
                        type_def = cls
                        break
                args = []
                for name in type_def[1:]:
                    accessor = getattr(self.z3_types.type_sort, name)
                    instance = simplify(accessor(z3_type))
                    args.append(self.unparse_annotation(instance))
                return '{}[{}]'.format(generic_name, ', '.join(args))
            return match.group(1)

        match = re.match("type", type_str)
        # unparse type type. Example: type_type(class_A) -> Type[A]
        if match:
            # get the instance of this type
            instance_accessor = getattr(self.z3_types.type_sort, "type_arg_0")
            instance = simplify(instance_accessor(z3_type))
            return "Type[{}]".format(self.unparse_annotation(instance))

        if type_str == "tuple_0":
            # unparse zero-length tuple. tuple_0 -> Tuple[()]
            return "Tuple[()]"

        match = re.match("tuple_(\d+)", type_str)
        if match:
            # unparse tuple type. tuple_2(int, list(int)) -> Tuple[int, List[int]]
            args = []
            tuple_len = int(match.group(1))
            for i in range(tuple_len):
                # Get the accessor for every tuple arg.
                arg_accessor = getattr(self.z3_types.type_sort, "tuple_{}_arg_{}".format(tuple_len, i + 1))
                arg = simplify(arg_accessor(z3_type))
                args.append(self.unparse_annotation(arg))

            args_str = ", ".join(args)
            return "Tuple[{}]".format(args_str)

        match = re.match("set", type_str)
        # unparse set type. set(int) -> Set[int]
        if match:
            set_type_accessor = self.z3_types.set_type
            set_type = simplify(set_type_accessor(z3_type))
            return "Set[{}]".format(self.unparse_annotation(set_type))

        match = re.match("dict", type_str)
        # unparse dict type. dict(int, str) -> Dict[int, str]
        if match:
            key_accessor = self.z3_types.dict_key_type
            val_accessor = self.z3_types.dict_value_type
            key_type = simplify(key_accessor(z3_type))
            val_type = simplify(val_accessor(z3_type))

            return "Dict[{}, {}]".format(self.unparse_annotation(key_type),
                                         self.unparse_annotation(val_type))

        match = re.match("func_(\d+)", type_str)
        # unparse func type. func_0(0, int, none) -> Callable[[int], None]
        if match:
            args = []
            args_len = int(match.group(1))
            for i in range(args_len):
                arg_accessor = getattr(self.z3_types.type_sort, "func_{}_arg_{}".format(args_len, i + 1))
                arg = simplify(arg_accessor(z3_type))
                args.append(self.unparse_annotation(arg))
            return_accessor = getattr(self.z3_types.type_sort, "func_{}_return".format(args_len))
            return_type = simplify(return_accessor(z3_type))
            return_annotation = self.unparse_annotation(return_type)

            return "Callable[[{}], {}]".format(", ".join(args), return_annotation)

        if type_str.startswith('tv'):
            tv_name = type_str[2:]
            if tv_name[0].isdigit():
                tv_name = 'T' + tv_name
            return tv_name

        return type_str
        #raise TypeError("Couldn't unparse type {}".format(type_str))
