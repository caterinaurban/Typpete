import ast
import frontend.stubs.stubs_paths as paths
from frontend.context import Context


class StubsHandler:
    def __init__(self):
        self.asts = []
        self.lib_asts = {}

        classes_and_functions_files = paths.classes_and_functions
        for file in classes_and_functions_files:
            r = open(file)
            tree = ast.parse(r.read())
            r.close()
            self.asts.append(tree)

        for lib in paths.libraries:
            r = open(paths.libraries[lib])
            tree = ast.parse(r.read())
            r.close()
            self.lib_asts[lib] = tree

    @staticmethod
    def infer_file(tree, solver, used_names, infer_func, method_type=None):
        # Infer only structs that are used in the program to be inferred

        # Function definitions
        relevant_nodes = StubsHandler.get_relevant_nodes(tree, used_names)

        context = Context(tree.body, solver)
        if method_type:
            # Add the flag in the statements to recognize the method statements during the inference
            for node in relevant_nodes:
                node.method_type = method_type

        for stmt in relevant_nodes:
            infer_func(stmt, context, solver)

        return context

    @staticmethod
    def get_relevant_nodes(tree, used_names):
        """Get relevant nodes (which are used in the program) from the given AST `tree`"""

        # Class definitions
        relevant_nodes = [node for node in tree.body
                           if (isinstance(node, ast.ClassDef) and
                               (node.name in used_names or StubsHandler.get_relevant_nodes(node, used_names)))]

        # TypeVar definitions
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.Assign) and
                               isinstance(node.value, ast.Call) and
                               isinstance(node.value.func, ast.Name) and
                               node.value.func.id == "TypeVar")]

        # Function definitions
        relevant_nodes += [node for node in tree.body
                          if (isinstance(node, ast.FunctionDef) and
                              node.name in used_names)]

        # Variable assignments
        # For example, math package has `pi` declaration as pi = 3.14...
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.Assign) and
                               any([isinstance(x, ast.Name) and
                                    x.id in used_names for x in node.targets]))]

        return relevant_nodes

    def get_relevant_ast_nodes(self, used_names):
        """Get the AST nodes which are used in the whole program stubs.
        
        These nodes are used in the pre-analysis.
        """
        relevant_nodes = []

        # Get nodes from normal classes and functions stubs.
        for tree in self.asts:
            current = self.get_relevant_nodes(tree, used_names)
            for node in current:
                node._module = tree
            relevant_nodes += current

        return relevant_nodes

    def infer_all_files(self, context, solver, used_names, infer_func):
        for tree in self.asts:
            ctx = self.infer_file(tree, solver, used_names, infer_func)
            # Merge the stub types into the context
            context.types_map.update(ctx.types_map)

    def infer_builtin_lib(self, module_name, solver, used_names, infer_func):
        """
        
        :param module_name: The name of the built-in library to be inferred 
        :param solver: The Z3 solver
        :param used_names: The names used in the program, to infer only relevant stubs.
        :param infer_func: The statements inference function
        :return: The context containing types of the relevant stubs.
        """
        if module_name not in self.lib_asts:
            raise ImportError("No module named {}".format(module_name))
        return self.infer_file(self.lib_asts[module_name], solver, used_names, infer_func)
