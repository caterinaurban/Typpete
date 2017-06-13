from z3 import Or


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

    @staticmethod
    def resolve_args(annotation):
        """Parse a comma-separated string into a list of arguments annotations
        
        Example:
            "int, str, List[int], Tuple[int, Tuple[str, float]]"
            --->
            ["int", "str", "List[int]", "Tuple[int, Tuple[str, float]]"]
        """
        count_brackets = 0
        args = []
        current_arg = ""
        for char in annotation:
            if char == "[":
                count_brackets += 1
            elif char == "]":
                count_brackets -= 1
            elif char == ",":
                if count_brackets == 0:
                    # Only count an argument if there's no mismatched brackets
                    # To prevent splitting in the middle of a type
                    args.append(current_arg)
                    current_arg = ""
                    continue
            if char != " ":
                current_arg += char

        if current_arg:
            args.append(current_arg)

        return args

    def resolve(self, annotation, solver, generics_map=None):
        """Resolve the type annotation with the following grammar:
        
        t = object | int | bool | float | complex | str | bytes | None
            | List[t]
            | Dict[t, t]
            | Set[t]
            | Type[t]
            | Tuple[t*]
            | Callable[[t*], t]
        """
        if annotation in self.primitives:  # check if it's primitive type
            return self.primitives[annotation]

        if annotation in self.z3_types.all_types:  # check if it's a user defined class
            return getattr(self.z3_types.type_sort, "class_{}".format(annotation))

        if annotation[:4] == "List":
            # Parse List type
            assert annotation[4] == "[" and annotation[-1] == "]"
            return self.z3_types.list(self.resolve(annotation[5:-1], solver, generics_map))

        if annotation[:4] == "Dict":
            # Parse Dict type
            assert annotation[4] == "[" and annotation[-1] == "]"

            # Get the types of the dict args
            args_annotations = self.resolve_args(annotation[5: -1])
            args_types = [self.resolve(arg, solver, generics_map) for arg in args_annotations]
            return self.z3_types.dict(*args_types)

        if annotation[:3] == "Set":
            # Parse Set type
            assert annotation[3] == "[" and annotation[-1] == "]"
            return self.z3_types.set(self.resolve(annotation[4:-1], solver, generics_map))
            pass

        if annotation[:4] == "Type" and annotation[4] == '[':
            # Parse Type type
            assert annotation[4] == "[" and annotation[-1] == "]"
            return self.z3_types.type(self.resolve(annotation[5:-1], solver, generics_map))
            pass

        if annotation[:5] == "Tuple":
            # Parse Tuple type
            assert annotation[5] == "[" and annotation[-1] == "]"

            # Get the types of the tuple args
            args_annotations = self.resolve_args(annotation[6:-1])
            args_types = [self.resolve(arg, solver, generics_map) for arg in args_annotations]
            return self.z3_types.tuples[len(args_types)](*args_types)

        if annotation[:8] == "Callable":
            # Parse Callable type
            assert annotation[8] == "[" and annotation[-1] == "]"

            # Extract the args and return annotations
            args_and_return = self.resolve_args(annotation[9:-1])
            assert len(args_and_return) == 2
            assert args_and_return[0][0] == "[" and args_and_return[0][-1] == "]"

            # Get the args and return types
            args_annotations = self.resolve_args(args_and_return[0][1:-1])
            args_types = [self.resolve(arg, solver, generics_map) for arg in args_annotations]
            return_type = self.resolve(args_and_return[1], solver, generics_map)

            return self.z3_types.funcs[len(args_types)](*(args_types + [return_type]))

        if annotation[:5] == "Union":
            # Parse Union type
            assert annotation[5] == "[" and annotation[-1] == "]"

            # Get the types of the union args
            args_annotations = self.resolve_args(annotation[6:-1])
            args_types = [self.resolve(arg, solver, generics_map) for arg in args_annotations]

            # The result of the union type is only one of args, Z3 picks the appropriate one
            # according to the added constraints.
            # Therefore, using more than one type from the union in the same program isn't yet supported.
            # For example, the following is not supported:
            # def f(x: Union[int, str]): ...
            # f(1)
            # f("str")
            result_type = solver.new_z3_const("union")
            solver.add(Or([result_type == arg for arg in args_types]),
                       fail_message="Union in type annotation")

            return result_type

        if generics_map is None:
            raise ValueError("Invalid type annotation: {}.".format(annotation))

        if annotation[:7] == "TypeVar":
            # The first encountered TypeVar for a specific type variable defines
            # its supertypes.
            # Example: TypeVar[T, [int, str]], defines a type variable T which has supertypes int and string
            assert annotation[7] == "[" and annotation[-1] == "]"
            args_annotations = self.resolve_args(annotation[8: -1])
            type_var_name = args_annotations[0]

            if type_var_name in generics_map:
                raise TypeError("Type variable {} is already defined before".format(type_var_name))

            supers_annotations = self.resolve_args(args_annotations[1][1:-1])
            supers_types = [self.resolve(x, solver, generics_map) for x in supers_annotations]
            result_type = solver.new_z3_const("generic")

            solver.add([solver.z3_types.subtype(result_type, x) for x in supers_types],
                       fail_message="Subtyping in type variable")

            generics_map[type_var_name] = result_type
            return result_type

        if annotation in generics_map:
            return generics_map[annotation]

        result_type = solver.new_z3_const("generic")
        generics_map[annotation] = result_type
        return result_type

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

        for i in range(len(args_annotations)):
            arg_type = self.resolve(args_annotations[i], solver, generics_map)
            solver.add(solver.z3_types.subtype(args_types[i], arg_type),
                       fail_message="Generic parameter type")

        solver.add(result_type == self.resolve(result_annotation, solver, generics_map),
                   fail_message="Generic return type")
