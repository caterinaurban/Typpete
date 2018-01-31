import ast

import sys

from collections import OrderedDict
from z3 import simplify
from z3.z3types import Z3Exception


class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, node, context_nodes, solver, name="", parent_context=None, is_class=False, is_func=False):
        """
        
        :param context_nodes: The AST nodes that belong to this scope. Used to pre-store all class types in the scope. 
        :param solver: The SMT solver for the inference. Used to create new Z3 constants for the class types.
        :param name: The context name
        :param parent_context: Reference to the parent scope (context)
        :param is_class: True if the context is a class local context
        """
        self.name = name
        self.is_class = is_class
        self.is_func = is_func
        self.types_map = {}
        self.isinstance_nodes = {}
        self.node = node
        self.context_nodes = context_nodes

        self.add_nodes(context_nodes, solver)

        self.builtin_methods = {}
        self.parent_context = parent_context
        self.children_contexts = []
        self.func_to_ast = {}
        self.assignments = []
        self.imports = set()

        self.used_type_vars = OrderedDict()

        if parent_context:
            parent_context.children_contexts.append(self)

    def add_nodes(self, context_nodes, solver):
        # Store all the class types that appear in this context. This enables using
        # classes in no specific order.
        class_names = [node.name for node in context_nodes if
                       isinstance(node, ast.ClassDef)]
        for cls in class_names:
            if cls in solver.z3_types.all_types:
                cls_type = solver.z3_types.all_types[cls]
                self.types_map[cls] = cls_type

        # Similarly, store function types that appear in this context
        func_names = [node.name for node in context_nodes if
                      isinstance(node, ast.FunctionDef)]
        for func in func_names:
            func_type = solver.new_z3_const("func")
            self.types_map[func] = func_type

    def get_type(self, var_name, passed_func=False):
        """Get the type of `var_name` from this context (or a parent context)"""
        if not passed_func:
            passed_func = self.is_func
        if var_name in self.types_map and not (self.is_class and passed_func):
            return self.types_map[var_name]
        if self.parent_context is None:
            raise NameError("Name {} is not defined.".format(var_name))
        return self.parent_context.get_type(var_name, passed_func)


    def get_isinstance_type(self, dump):
        if dump in self.isinstance_nodes:
            return self.isinstance_nodes[dump]
        if self.parent_context is None:
            raise NameError("Cannot find isinstance node")
        return self.parent_context.get_isinstance_type(dump)


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
        if var_name in self.types_map and not self.is_class:
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

    def should_remove(self, node):
        if hasattr(node, 'super') and node.super != self.name:
            return True
        if hasattr(node, 'remove_later') and node.remove_later:
            return True
        return False

    def remove_extra_nodes(self):
        to_remove = [x for x in self.context_nodes if self.should_remove(x)]
        for node in to_remove:
            self.context_nodes.remove(node)
            if isinstance(node, ast.FunctionDef) and node.name in self.func_to_ast:
                del self.func_to_ast[node.name]

        for child in self.children_contexts:
            child.remove_extra_nodes()

    def generate_typed_ast(self, model, solver):
        """Add type annotations for all functions and assignments statements"""
        self.remove_extra_nodes()
        self.add_annotations_to_funcs(model, solver)
        self.add_annotations_to_classes(model, solver)
        self.add_annotation_to_assignments(model, solver)
        self.add_type_var_assigns(model, solver)

    def add_func_ast(self, func_name, ast_node):
        """Map a function with name `func_name` fo its corresponding AST node"""
        self.func_to_ast[func_name] = ast_node

    def add_annotations_to_classes(self, model, solver):
        if isinstance(self.node, ast.Module):
            for cls in [n for n in self.node.body if isinstance(n, ast.ClassDef)]:
                if cls.name in solver.z3_types.config.class_type_params:
                    args = []
                    for name in solver.z3_types.config.class_type_params[cls.name]:
                        real_name = str(name)
                        z3_name = 'tv' + real_name
                        tvar_lit = getattr(solver.z3_types.type_sort, z3_name)
                        if z3_name not in self.used_type_vars:
                            upper = solver.z3_types.upper(tvar_lit)
                            upper = solver.annotation_resolver.unparse_annotation(
                                model.evaluate(upper))
                            self.used_type_vars[z3_name] = upper
                        if real_name[0].isdigit():
                            real_name = 'T' + real_name
                        args.append(ast.Name(id=real_name))
                    if len(args) == 1:
                        slice = ast.Index(value=args[0])
                    else:
                        slice = ast.Index(ast.Tuple(elts=args))
                    cls.bases.append(ast.Subscript(value=ast.Name(id='Generic'), slice=slice))

    def add_type_var_assigns(self, model, solver):
        if isinstance(self.node, ast.Module):
            after_imports = 0
            while after_imports < len(self.node.body) and isinstance(self.node.body[after_imports], (ast.Import, ast.ImportFrom)):
                after_imports += 1
            for tv, upper in self.used_type_vars.items():
                tv_name = tv[2:]
                if tv_name[0].isdigit():
                    tv_name = 'T' + tv_name
                tv_decl = self._create_type_var_assign(tv_name, upper)
                self.node.body.insert(after_imports, tv_decl)
                after_imports += 1

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
            func_len = len(node.args.args)
            if inferred_type_name.startswith("generic"):
                nargs = int(inferred_type_name[7:8])
                arg_accessor_func = lambda i, n: lambda x: getattr(type_sort, "func_{}_arg_{}".format(n, i))(getattr(type_sort, 'generic{}_func'.format(nargs))(x))
                return_accessor_func = lambda n: lambda x: getattr(type_sort, "func_{}_return".format(n))(getattr(type_sort, 'generic{}_func'.format(nargs))(x))
                for arg in range(1, nargs + 1):
                    tvar_lit = simplify(getattr(type_sort, inferred_type_name[:8] + '_tv' + str(arg))(inferred_type))
                    tvar = str(tvar_lit)
                    if tvar not in self.used_type_vars:
                        upper = solver.z3_types.upper(tvar_lit)
                        upper = solver.annotation_resolver.unparse_annotation(model.evaluate(upper))
                        self.used_type_vars[tvar] = upper

            else:
                arg_accessor_func = lambda i, n: getattr(type_sort, "func_{}_arg_{}".format(n, i))
                return_accessor_func = lambda n: getattr(type_sort, "func_{}_return".format(n))


            # Add the type annotations for the function arguments
            for i, arg in enumerate(node.args.args):
                arg_type = simplify(arg_accessor_func(i + 1, func_len)(inferred_type))

                # Get the annotation with PEP 484 syntax
                arg_annotation_str = solver.annotation_resolver.unparse_annotation(arg_type)
                # Add the type annotation as an AST node
                arg.annotation = ast.parse(arg_annotation_str).body[0].value

                names = {name.id for name in list(ast.walk(arg.annotation)) if isinstance(name, ast.Name)}
                self.imports |= names

            # Similarly, add the return type annotation
            return_type = simplify(return_accessor_func(func_len)(inferred_type))
            return_annotation_str = solver.annotation_resolver.unparse_annotation(return_type)
            node.returns = ast.parse(return_annotation_str).body[0].value

            names = {name.id for name in list(ast.walk(node.returns)) if isinstance(name, ast.Name)}
            self.imports |= names


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
            if (len(node.targets) == 1
               and sys.version_info[0] >= 3 and sys.version_info[1] >= 6):
                # Replace the normal assignment node with annotated assignment
                # Annotated assignment only supports single assignment (no tuples or lists)
                # To unparse the assignment statement into the new syntax of the variable annotation,
                # The class of the nodes needs to be AnnAssign, to be recognized by the unparser
                z3_t = simplify(z3_t)
                if isinstance(node.targets[0], ast.Tuple):
                    try:
                        # Unfold tuple assignment
                        assigns = get_unfolded_assignments(node.targets[0], node.value, z3_t, model, solver)
                        if not assigns or node not in self.context_nodes:
                            continue
                        idx = self.context_nodes.index(node)
                        self.context_nodes.remove(node)
                        for assign in reversed(assigns):
                            self.context_nodes.insert(idx, assign)
                    except:
                        pass
                    continue
                try:
                    z3_t = model[z3_t] if model[z3_t] is not None else z3_t
                except Z3Exception:
                    continue
                node.__class__ = ast.AnnAssign
                node.target = node.targets[0]
                node.simple = 1
                annotation_str = solver.annotation_resolver.unparse_annotation(z3_t)
                node.annotation = ast.parse(annotation_str).body[0].value

                names = {name.id for name in list(ast.walk(node.annotation)) if isinstance(name, ast.Name)}
                self.imports |= names

        # Add the type comment for assignments in children contexts
        for child in self.children_contexts:
            child.add_annotation_to_assignments(model, solver)

    def get_imports(self):
        result = set()
        for child in self.children_contexts:
            result |= child.get_imports()
        return result | self.imports

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


def get_unfolded_assignments(node, value, z3_t, model, solver):
    if isinstance(node, ast.Tuple):
        if not isinstance(value, ast.Tuple):
            return [ast.Assign(
                targets=[node],
                value=value
            )]
        tuple_len = len(node.elts)
        nodes = []
        for i in range(tuple_len):
            arg_accessor = getattr(solver.z3_types.type_sort, "tuple_{}_arg_{}".format(tuple_len, i + 1))
            arg_z3_t = arg_accessor(z3_t)
            cur = get_unfolded_assignments(node.elts[i], value.elts[i], arg_z3_t, model, solver)
            nodes += cur
        return nodes
    elif isinstance(node, (ast.Name, ast.Attribute)):
        z3_t = simplify(z3_t)
        z3_t = model[z3_t] if model[z3_t] is not None else z3_t
        annotation_str = solver.annotation_resolver.unparse_annotation(z3_t)
        annotation = ast.parse(annotation_str).body[0].value
        node = ast.AnnAssign(
            target=node,
            value=value,
            annotation=annotation,
            simple=1
        )
        return [node]
    else:
        return [ast.Assign(
            targets=[node],
            value=value
        )]



class AnnotatedFunction:
    def __init__(self, args_annotations, return_annotation, defaults_count, module):
        self.args_annotations = args_annotations
        self.return_annotation = return_annotation
        self.defaults_count = defaults_count
        self.module = module
