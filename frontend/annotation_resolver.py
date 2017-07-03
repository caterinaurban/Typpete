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

    def resolve(self, annotation, solver):
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
            return self.z3_types.list(self.resolve(annotation[5:-1], solver))

        if annotation[:4] == "Dict":
            # Parse Dict type
            assert annotation[4] == "[" and annotation[-1] == "]"

            # Get the types of the dict args
            args_annotations = self.resolve_args(annotation[5: -1])
            args_types = [self.resolve(arg, solver) for arg in args_annotations]
            return self.z3_types.dict(*args_types)

        if annotation[:3] == "Set":
            # Parse Set type
            assert annotation[3] == "[" and annotation[-1] == "]"
            return self.z3_types.set(self.resolve(annotation[4:-1], solver))
            pass

        if annotation[:4] == "Type":
            # Parse Type type
            assert annotation[4] == "[" and annotation[-1] == "]"
            return self.z3_types.type(self.resolve(annotation[5:-1], solver))
            pass

        if annotation[:5] == "Tuple":
            # Parse Tuple type
            assert annotation[5] == "[" and annotation[-1] == "]"

            # Get the types of the tuple args
            args_annotations = self.resolve_args(annotation[6:-1])
            args_types = [self.resolve(arg, solver) for arg in args_annotations]
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
            args_types = [self.resolve(arg, solver) for arg in args_annotations]
            return_type = self.resolve(args_and_return[1], solver)

            return self.z3_types.funcs[len(args_types)](*([0] + args_types + [return_type]))

        if annotation[:5] == "Union":
            # Parse Union type
            assert annotation[5] == "[" and annotation[-1] == "]"

            # Get the types of the union args
            args_annotations = self.resolve_args(annotation[6:-1])
            args_types = [self.resolve(arg, solver) for arg in args_annotations]

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

        raise ValueError("Invalid type annotation: {}.".format(annotation))
