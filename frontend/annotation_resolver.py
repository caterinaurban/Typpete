from z3 import Or
import ast



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
            "None": z3_types.none,
            "number": z3_types.num,
            "sequence": z3_types.seq
        }
        self.type_var_poss = {}
        self.type_var_super = {}

    def resolve(self, annotation, solver, generics_map=None):
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
        if isinstance(annotation, ast.Name):
            if annotation.id in self.primitives:
                return self.primitives[annotation.id]
            if annotation.id in self.z3_types.all_types:
                return getattr(self.z3_types.type_sort, "class_{}".format(annotation.id))
            
            # Check if it's a generic type var
            if generics_map is None:
                raise ValueError("Invalid type annotation {} in line {}".format(annotation.id, annotation.lineno))
            if annotation.id in generics_map:
                return generics_map[annotation.id]
            if annotation.id not in self.type_var_poss:
                raise ValueError("Invalid type annotation {} in line {}".format(annotation.id, annotation.lineno))

            result_type = solver.new_z3_const("generic")
            generics_map[annotation.id] = result_type

            possible_types = [self.resolve(x, solver, generics_map) for x in self.type_var_poss[annotation.id]]
            if possible_types:
                solver.add(Or([result_type == x for x in possible_types]),
                           fail_message="Generic type in line {}".format(annotation.lineno))

            if annotation.id in self.type_var_super:
                type_var_super = self.resolve(self.type_var_super[annotation.id], solver, generics_map)
                solver.add(solver.z3_types.subtype(result_type, type_var_super),
                           fail_message="Generic bound in line {}".format(annotation.lineno))
            return result_type

        if isinstance(annotation, ast.Subscript):
            if not (isinstance(annotation.value, ast.Name) and isinstance(annotation.slice, ast.Index)):
                raise TypeError("Invalid type annotation in line {}.".format(annotation.lineno))

            annotation_val = annotation.value.id
            if annotation_val == "List":
                # Parse List type
                return self.z3_types.list(self.resolve(annotation.slice.value, solver, generics_map))
            
            if annotation_val == "Dict":
                # Parse Dict type
                if not (isinstance(annotation.slice.value, ast.Tuple) and len(annotation.slice.value.elts) == 2):
                    raise TypeError("Dict annotation in line {} should have 2 comma-separated args"
                                    .format(annotation.lineno))

                # Get the types of the dict args
                keys_type = self.resolve(annotation.slice.value.elts[0], solver, generics_map)
                vals_type = self.resolve(annotation.slice.value.elts[1], solver, generics_map)
                return self.z3_types.dict(keys_type, vals_type)
            
            if annotation_val == "Set":
                # Parse Set type
                return self.z3_types.set(self.resolve(annotation.slice.value, solver, generics_map))
            
            if annotation_val == "Type":
                # Parse Type type
                return self.z3_types.type(self.resolve(annotation.slice.value, solver, generics_map))
            
            if annotation_val == "Tuple":
                # Parse Tuple type
                if not isinstance(annotation.slice.value, (ast.Name, ast.Tuple)):
                    raise TypeError("Invalid tuple type annotation in line {}".format(annotation.lineno))

                # Get the types of the tuple args
                if isinstance(annotation.slice.value, ast.Name):
                    tuple_args_types = [self.resolve(annotation.slice.value, solver, generics_map)]
                else:
                    tuple_args_types = [self.resolve(x, solver, generics_map) for x in annotation.slice.value.elts]

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
                args_types = [self.resolve(x, solver, generics_map) for x in args_annotations]
                return_type = self.resolve(annotation.slice.value.elts[1], solver, generics_map)

                return self.z3_types.funcs[len(args_types)](*(args_types + [return_type]))

            if annotation_val == "Union":
                # Parse Union type
                if not isinstance(annotation.slice.value, (ast.Name, ast.Tuple)):
                    raise TypeError("Invalid union type annotation in line {}".format(annotation.lineno))

                # Get the types of the union args
                if isinstance(annotation.slice.value, ast.Name):
                    union_args_types = [self.resolve(annotation.slice.value, solver, generics_map)]
                else:
                    union_args_types = [self.resolve(x, solver, generics_map) for x in annotation.slice.value.elts]

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

        raise ValueError("Invalid type annotation in line {}".format(annotation.lineno))

    def add_annotated_function_axioms(self, args_types, solver, annotations, result_type):
        """Add axioms for a function call to an annotated function
        
        Reprocess the type annotations for every function call to prevent binding a certain type
        to the function definition
        """
        args_annotations = annotations[0]
        result_annotation = annotations[1]

        if len(args_types) != len(args_annotations):
            raise TypeError("The function expects {} arguments. {} were given.".format(len(args_annotations),
                                                                                       len(args_types)))
        generics_map = {}

        for i, annotation in enumerate(args_annotations):
            arg_type = self.resolve(annotation, solver, generics_map)
            solver.add(solver.z3_types.subtype(args_types[i], arg_type),
                       fail_message="Generic parameter type in line {}".format(annotation.lineno))
            solver.optimize.add_soft(args_types[i] == arg_type)

        solver.add(result_type == self.resolve(result_annotation, solver, generics_map),
                   fail_message="Generic return type in line {}".format(result_annotation.lineno))

    def add_type_var(self, target, type_var_node):
        if not isinstance(target, ast.Name):
            raise TypeError("TypeVar assignment target should be a variable name.")
        if not type_var_node.args:
            raise TypeError("Invalid type variable declaration in line {}.".format(type_var_node.lineno))
        args = type_var_node.args
        if not isinstance(args[0], ast.Str):
            raise TypeError("Name of type variable in line {} should be a string".format(type_var_node.lineno))
        type_var_name = target.id
        type_var_possibilities = args[1:]

        if type_var_node.keywords and type_var_node.keywords[0].arg == "bound":
            type_var_super = type_var_node.keywords[0].value
            self.type_var_super[type_var_name] = type_var_super

        if len(type_var_possibilities) == 1:
            raise TypeError("A single constraint is not allowed in TypeVar in line {}".format(type_var_node.lineno))

        self.type_var_poss[type_var_name] = type_var_possibilities
