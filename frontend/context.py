import ast

import sys

from z3 import simplify


class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, context_nodes, solver, name="", parent_context=None):
        """
        
        :param context_nodes: The AST nodes that belong to this scope. Used to pre-store all class types in the scope. 
        :param solver: The SMT solver for the inference. Used to create new Z3 constants for the class types.
        :param name: The context name
        :param parent_context: Reference to the parent scope (context)
        """
        self.name = name
        self.types_map = {}

        # Store all the class types that appear in this context. This enables using
        # classes in no specific order.
        class_names = [node.name for node in context_nodes if isinstance(node, ast.ClassDef)]
        for cls in class_names:
            cls_type = solver.new_z3_const("class_type")
            self.types_map[cls] = cls_type
            solver.z3_types.all_types[cls] = cls_type

        # Similarly, store function types that appear in this context
        func_names = [node.name for node in context_nodes if isinstance(node, ast.FunctionDef)]
        for func in func_names:
            func_type = solver.new_z3_const("func")
            self.types_map[func] = func_type

        self.builtin_methods = {}
        self.parent_context = parent_context
        self.children_contexts = []
        self._type_params = {}
        self.func_to_ast = {}
        self.assignments = []

        if parent_context:
            parent_context.children_contexts.append(self)

    @property
    def type_params(self):
        if self.parent_context:
            return self.parent_context.type_params
        else:
            return self._type_params

    @type_params.setter
    def type_params(self, tp):
        self._type_params = tp

    @property
    def class_type_params(self):
        if self.parent_context:
            return self.parent_context.class_type_params
        else:
            return self._class_type_params

    @class_type_params.setter
    def class_type_params(self, tp):
        self._class_type_params = tp

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

    def _create_type_var_assign(self, name, upper):
        target = ast.Name(id=name)
        tv_func = ast.Name(id="TypeVar")
        name_str = ast.Str(s=name)
        bound_name = ast.Name(id=upper)
        upper_kw = ast.keyword(arg="bound", value=bound_name)
        value = ast.Call(func=tv_func,args=[name_str], keywords=[upper_kw])
        res = ast.Assign(targets=[target], value=value)
        return res

    def add_annotations_to_funcs(self, model, solver):
        """Add the function types given by the SMT model as annotations to the AST nodes"""
        type_sort = solver.z3_types.type_sort
        for func, node in self.func_to_ast.items():
            z3_t = self.types_map[func]
            inferred_type = model[z3_t]
            inferred_type_name = str(inferred_type)
            if inferred_type_name.startswith("generic"):
                if hasattr(node, '_parent') and hasattr(node._parent, 'body'):
                    nargs = int(inferred_type_name[7:8])
                    for arg in range(1, nargs + 1):
                        tvar = simplify(getattr(type_sort, inferred_type_name[:8] + '_tv' + str(arg))(inferred_type))
                        upper = solver.z3_types.upper(tvar)
                        upper = solver.annotation_resolver.unparse_annotation(model.evaluate(upper))
                        assign = self._create_type_var_assign("T{}".format(str(tvar)[2:]), upper)
                        index = node._parent.body.index(node)
                        node._parent.body.insert(index, assign)
                inferred_type = getattr(type_sort, inferred_type_name[:8] + "_func")(inferred_type)


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
            if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
               and sys.version_info[0] >= 3 and sys.version_info[1] >= 6):
                # Replace the normal assignment node with annotated assignment
                # Annotated assignment only supports single assignment (no tuples or lists)
                # To unparse the assignment statement into the new syntax of the variable annotation,
                # The class of the nodes needs to be AnnAssign, to be recognized by the unparser
                node.__class__ = ast.AnnAssign
                node.target = node.targets[0]
                node.simple = 1
                annotation_str = solver.annotation_resolver.unparse_annotation(
                    model[self.get_type(node.targets[0].id)])
                node.annotation = ast.parse(annotation_str).body[0].value

        # Add the type comment for assignments in children contexts
        for child in self.children_contexts:
            child.add_annotation_to_assignments(model, solver)

    def get_matching_methods(self, method_name):
        """Return the built-in methods in this context (or a parent context) which match the given method name"""
        methods = []
        for t in self.builtin_methods:
            if method_name in self.builtin_methods[t]:
                methods.append(self.builtin_methods[t][method_name])
        if self.parent_context is None:
            return methods
        return methods + self.parent_context.get_matching_methods(method_name)

    def has_context_in_children(self, context_name):
        """Check if this context or one of the children contexts matches the given name."""
        if self.name == context_name:
            return True
        for child in self.children_contexts:
            if child.name == context_name:
                return True
        return False

    def get_context_from_children(self, context_name):
        """Get the context matching the given name."""
        if self.name == context_name:
            return self
        for child in self.children_contexts:
            if child.name == context_name:
                return child
        raise NameError("Context {} is not defined".format(context_name))


class AnnotatedFunction:
    def __init__(self, args_annotations, return_annotation, defaults_count):
        self.args_annotations = args_annotations
        self.return_annotation = return_annotation
        self.defaults_count = defaults_count
