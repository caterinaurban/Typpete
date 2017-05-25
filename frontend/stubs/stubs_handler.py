from frontend.stmt_inferrer import infer
import ast


class StubsHandler:
    def __init__(self):
        self.files = ["frontend/stubs/functions.py"]

    @staticmethod
    def infer_file(file, context, solver):
        r = open(file)
        t = ast.parse(r.read())

        for stmt in t.body:
            infer(stmt, context, solver)

    def infer_all_files(self, context, solver):
        for file in self.files:
            self.infer_file(file, context, solver)
