from frontend.stmt_inferrer import infer
import ast


class StubsHandler:
    def __init__(self, pre_analyzer):
        self.files = ["frontend/stubs/functions.py"]
        self.asts = []

        for file in self.files:
            r = open(file)
            tree = ast.parse(r.read())
            pre_analyzer.add_stub_ast(tree)
            self.asts.append(tree)

    @staticmethod
    def infer_file(tree, context, solver, used_names):
        # Infer only structs that are used in the program to be inferred

        # Function definitions
        relevant_nodes = [node for node in tree.body
                          if (isinstance(node, ast.FunctionDef) and
                              node.name in used_names)]

        # Class definitions
        relevant_nodes += [node for node in tree.body
                           if (isinstance(node, ast.ClassDef) and
                               node.name in used_names)]

        for stmt in relevant_nodes:
            infer(stmt, context, solver)

    def infer_all_files(self, context, solver, used_names):
        for tree in self.asts:
            self.infer_file(tree, context, solver, used_names)
