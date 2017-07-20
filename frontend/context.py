import ast
from z3 import simplify

class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, parent_context=None):
        self.types_map = {}
        self.builtin_methods = {}
        self.parent_context = parent_context
        self.children_contexts = []
        self.func_to_ast = {}
        self.assignments = []

        if parent_context:
            parent_context.children_contexts.append(self)

    def get_type(self, var_name):
        """Get the type of `var_name` from this context (or a parent context)"""
        if var_name in self.types_map:
            return self.types_map[var_name]
        if self.parent_context is None:
            raise NameError("Name {} is not defined.".format(var_name))
        return self.parent_context.get_type(var_name)

    def set_type(self, var_name, var_type):
        """Sets the type of a variable in this context."""
        self.types_map[var_name] = var_type

    def delete_type(self, var_name):
        """Delete the variable `var_name` from this context (or a parent context)"""
        if var_name in self.types_map:
            del self.types_map[var_name]
        elif self.parent_context is None:
            raise NameError("Name {} is not defined.".format(var_name))
        else:
            self.parent_context.delete_type(var_name)

    def has_variable(self, var_name):
        """Check if this context (or parent context) has a variable `var_name`"""
        if var_name in self.types_map:
            return True
        if self.parent_context is None:
            return False
        return self.parent_context.has_variable(var_name)

    def has_var_in_children(self, var_name):
        """Check if the variable exists in this context or in children contexts"""
        if var_name in self.types_map:
            return True
        for child in self.children_contexts:
            if child.has_var_in_children(var_name):
                return True
        return False

    def get_var_from_children(self, var_name):
        """Get variable type from this context or from children contexts"""
        if var_name in self.types_map:
            return self.types_map[var_name]
        for child in self.children_contexts:
            try:
                return child.get_var_from_children(var_name)
            except NameError:
                continue
        raise NameError("Name {} is not defined".format(var_name))

    def generate_typed_ast(self, model, solver):
        """Add type annotations for all functions and assignments statements"""
        self.add_annotations_to_funcs(model, solver)
        self.add_annotation_to_assignments(model, solver)

    def add_func_ast(self, func_name, ast_node):
        """Map a function with name `func_name` fo its corresponding AST node"""
        self.func_to_ast[func_name] = ast_node

    def add_annotations_to_funcs(self, model, solver):
        """Add the function types given by the SMT model as annotations to the AST nodes"""
        type_sort = solver.z3_types.type_sort
        for func, node in self.func_to_ast.items():
            z3_t = self.types_map[func]
            inferred_type = model[z3_t]
            func_len = len(node.args.args)

            # Add the type annotations for the function arguments
            for i, arg in enumerate(node.args.args):
                arg_accessor = getattr(type_sort, "func_{}_arg_{}".format(func_len, i + 1))
                arg_type = simplify(arg_accessor(inferred_type))

                # Get the annotation with PEP 484 syntax
                arg_annotation_str = solver.annotation_resolver.unparse_annotation(arg_type)

                # Add the type annotation as an AST node
                arg.annotation = ast.parse(arg_annotation_str).body[0].value

            # Similarly, add the return type annotation
            return_accessor = getattr(type_sort, "func_{}_return".format(func_len))
            return_type = simplify(return_accessor(inferred_type))
            return_annotation_str = solver.annotation_resolver.unparse_annotation(return_type)
            node.returns = ast.parse(return_annotation_str).body[0].value

        # Add the type annotations for functions in children contexts
        for child in self.children_contexts:
            child.add_annotations_to_funcs(model, solver)

    def add_assignment(self, z3_value_type, ast_node):
        """Add assignment statement node along with its z3 type to the context

        At the end of the inference, add the type comment to every assignment node.
        """
        self.assignments.append((ast_node, z3_value_type))

    def add_annotation_to_assignments(self, model, solver):
        """Add a type comment for every assignment statement in the context"""
        for node, z3_t in self.assignments:
            inferred_type = model[z3_t]
            node.type_comment = solver.annotation_resolver.unparse_annotation(inferred_type)

        # Add the type comment for assignments in children contexts
        for child in self.children_contexts:
            child.add_annotation_to_assinments(model, solver)

    def get_matching_methods(self, method_name):
        """Return the built-in methods in this context (or a parent context) which match the given method name"""
        methods = []
        for t in self.builtin_methods:
            if method_name in self.builtin_methods[t]:
                methods.append(self.builtin_methods[t][method_name])
        if self.parent_context is None:
            return methods
        return methods + self.parent_context.get_matching_methods(method_name)


class AnnotatedFunction:
    def __init__(self, args_annotations, return_annotation):
        self.args_annotations = args_annotations
        self.return_annotation = return_annotation
