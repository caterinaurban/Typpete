from frontend.stmt_inferrer import infer
import ast


class StubsHandler:
    def __init__(self):
        self.files = ["frontend/stubs/functions.py"]

    @staticmethod
    def infer_file(file, context, solver, used_names):
        r = open(file)
        t = ast.parse(r.read())

        # Infer only structs that are used in the program to be inferred

        # Function definitions
        relevant_nodes = [node for node in t.body
                          if (isinstance(node, ast.FunctionDef) and
                              node.name in used_names)]

        # Class definitions
        relevant_nodes += [node for node in t.body
                           if (isinstance(node, ast.ClassDef) and
                               node.name in used_names)]

        for stmt in relevant_nodes:
            infer(stmt, context, solver)

    def infer_all_files(self, context, solver, used_names):
        for file in self.files:
            self.infer_file(file, context, solver, used_names)
