import ast


class PreAnalyzer:
    """Analyzer for the AST to give some configurations before the type inference"""

    def __init__(self, prog_ast):
        """
        :param prog_ast: The AST for the python program  
        """

        # List all the nodes existing in the AST
        self.all_nodes = list(ast.walk(prog_ast))

    def maximum_function_args(self):
        """Get the maximum number of function arguments appearing in the AST"""
        func_defs = [node for node in self.all_nodes if isinstance(node, ast.FunctionDef)]
        return 0 if len(func_defs) == 0 else max([len(node.args.args) for node in func_defs])

    def maximum_tuple_length(self):
        """Get the maximum length of tuples appearing in the AST"""
        tuples = [node for node in self.all_nodes if isinstance(node, ast.Tuple)]
        return 0 if len(tuples) == 0 else max([len(node.elts) for node in tuples])

    def classes_pre_analysis(self):
        # TODO propagate attributes to subclasses.
        class_defs = [node for node in self.all_nodes if isinstance(node, ast.ClassDef)]
        class_to_attributes = {}
        class_to_base = {}

        for cls in class_defs:
            if len(cls.bases) > 1:
                raise NotImplementedError("Multiple inheritance is not supported yet.")
            elif len(cls.bases) == 1:
                class_to_base[cls.name] = cls.bases[0].id
            else:
                class_to_base[cls.name] = "object"

            attributes = set()
            class_to_attributes[cls.name] = attributes

            # Inspect all class-level statements
            for cls_stmt in cls.body:
                if isinstance(cls_stmt, ast.FunctionDef):
                    # Add function to class attributes and get attributes defined by self.some_attribute = value
                    attributes.add(cls_stmt.name)
                    if len(cls_stmt.args.args) == 0:
                        continue
                    first_arg = cls_stmt.args.args[0].arg  # In most cases it will be 'self'

                    # Get attribute assignments where attribute value is the same as the first argument
                    func_nodes = ast.walk(cls_stmt)
                    assignments = [node for node in func_nodes if isinstance(node, ast.Assign)]

                    for assignment in assignments:
                        for target in assignment.targets:
                            if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and
                                    target.value.id == first_arg):
                                attributes.add(target.attr)
                elif isinstance(cls_stmt, ast.Assign):
                    # Get attributes defined as class-level assignment
                    for target in cls_stmt.targets:
                        if isinstance(target, ast.Name):
                            attributes.add(target.id)

        return class_to_attributes, class_to_base
