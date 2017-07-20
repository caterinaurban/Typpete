import ast
import frontend.stubs.stubs_paths as paths


class StubsHandler:
    def __init__(self, pre_analyzer):
        self.asts = []
        self.methods_asts = []
        self.lib_asts = {}

        classes_and_functions_files = paths.classes_and_functions
        for file in classes_and_functions_files:
            r = open(file)
            tree = ast.parse(r.read())
            r.close()
            pre_analyzer.add_stub_ast(tree)
            self.asts.append(tree)

        for method in paths.methods:
            r = open(method["path"])
            tree = ast.parse(r.read())
            r.close()
            pre_analyzer.add_stub_ast(tree)
            tree.method_type = method["type"]
            self.methods_asts.append(tree)

        for lib in paths.libraries:
            r = open(paths.libraries[lib])
            tree = ast.parse(r.read())
            r.close()
            pre_analyzer.add_stub_ast(tree)
            self.lib_asts[lib] = tree

    @staticmethod
    def infer_file(tree, context, solver, used_names, infer_func, method_type=None):
        # Infer only structs that are used in the program to be inferred

        # Function definitions
        relevant_nodes = [node for node in tree.body
                          if (isinstance(node, ast.FunctionDef) and
                              node.name in used_names)]

        # Class definitions
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.ClassDef) and
                               node.name in used_names)]

        # TypeVar definitions
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.Assign) and
                               isinstance(node.value, ast.Call) and
                               isinstance(node.value.func, ast.Name) and
                               node.value.func.id == "TypeVar")]

        # Variable assignments
        # For example, math package has `pi` declaration as pi = 3.14...
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.Assign) and
                               any([isinstance(x, ast.Name) and
                                    x.id in used_names for x in node.targets]))]

        if method_type:
            # Add the flag in the statements to recognize the method statements during the inference
            for node in relevant_nodes:
                node.method_type = method_type

        for stmt in relevant_nodes:
            infer_func(stmt, context, solver)

    def infer_all_files(self, context, solver, used_names, infer_func):
        for tree in self.asts:
            self.infer_file(tree, context, solver, used_names, infer_func)
        for tree in self.methods_asts:
            self.infer_file(tree, context, solver, used_names, infer_func, tree.method_type)

    def infer_builtin_lib(self, module_name, context, solver, used_names, infer_func):
        if module_name not in self.lib_asts:
            raise ImportError("No module named {}".format(module_name))
        self.infer_file(self.lib_asts[module_name], context, solver, used_names, infer_func)
