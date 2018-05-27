import ast
import os
import typpete.src.stubs.stubs_paths as paths
from typpete.src.context import Context

INFERRED = {}
STUB_ASTS = {}

class StubsHandler:
    def __init__(self):
        self.asts = []
        self.lib_asts = {}
        self.methods_asts = []
        cur_directory = os.path.dirname(__file__)
        classes_and_functions_files = paths.classes_and_functions
        for file in classes_and_functions_files:
            path = cur_directory + '/' + file
            r = open(path)
            tree = ast.parse(r.read())
            r.close()
            STUB_ASTS[path] = tree
            self.asts.append(tree)

        for method in paths.methods:
            path = cur_directory + '/' + method["path"]
            r = open(path)
            tree = ast.parse(r.read())
            r.close()
            STUB_ASTS[path] = tree
            tree.method_type = method["type"]
            self.methods_asts.append(tree)

        for lib in paths.libraries:
            path = cur_directory + '/' + paths.libraries[lib]
            r = open(path)
            tree = ast.parse(r.read())
            r.close()
            STUB_ASTS[path] = tree
            self.lib_asts[lib] = tree

    def infer_file(self, tree, solver, used_names, infer_func, method_type=None):
        # Infer only structs that are used in the program to be inferred

        # Function definitions
        if tree in INFERRED:
            return INFERRED[tree]
        relevant_nodes = self.get_relevant_nodes(tree, used_names)

        context = Context(tree, tree.body, solver)
        INFERRED[tree] = context

        if method_type:
            # Add the flag in the statements to recognize the method statements during the inference
            for node in relevant_nodes:
                node.method_type = method_type

        for stmt in relevant_nodes:
            infer_func(stmt, context, solver)

        return context

    def get_relevant_nodes(self, tree, used_names, global_ctx=False):
        """Get relevant nodes (which are used in the program) from the given AST `tree`"""

        # Class definitions
        if not global_ctx:
            relevant_nodes = [node for node in tree.body
                              if (isinstance(node, ast.ClassDef) and
                                  (node.name in used_names or self.get_relevant_nodes(node, used_names)))]
        else:
            relevant_nodes = [node for node in tree.body
                              if (isinstance(node, ast.ClassDef))]


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

        name_nodes = [x.id for node in relevant_nodes for x in ast.walk(node) if isinstance(x, ast.Name)]
        import_nodes = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        for node in import_nodes:
            appended = False
            if node.module == 'typing':
                # FIXME remove after added typing stub
                continue
            for name in node.names:
                if name.name in name_nodes and not appended:
                    appended = True
                    relevant_nodes.append(self.lib_asts[node.module])
                    relevant_nodes.append(node)
                    used_names.append(name.name)


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
            current = self.get_relevant_nodes(tree, used_names, True)
            relevant_nodes += current

        # Get nodes from builtin methods stubs.
        for tree in self.methods_asts:
            relevant_nodes += self.get_relevant_nodes(tree, used_names)

        return relevant_nodes

    def infer_all_files(self, context, solver, used_names, infer_func):
        for tree in self.asts:
            ctx = self.infer_file(tree, solver, used_names, infer_func)
            # Merge the stub types into the context
            context.types_map.update(ctx.types_map)

        for tree in self.methods_asts:
            ctx = self.infer_file(tree, solver, used_names, infer_func,
                                  tree.method_type)
            context.builtin_methods.update(ctx.builtin_methods)

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
        lib_ast = self.lib_asts[module_name]
        all_nodes = ast.walk(lib_ast)
        for n in all_nodes:
            n._module = lib_ast
        return self.infer_file(lib_ast, solver, used_names, infer_func)
