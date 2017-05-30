import ast
from frontend.context import Context


class ImportHandler:
    def infer_import_from(self, module_name, relative_level, names):
        if not relative_level and self.is_builtin(module_name):
            # TODO import builtins
            pass
        # TODO

    @staticmethod
    def get_ast(module_name, base_folder):
        r = open("{}/{}.py".format(base_folder, module_name))
        return ast.parse(r.read())

    @staticmethod
    def infer_import(module_name, base_folder, infer_func, solver):
        t = ImportHandler.get_ast(module_name, base_folder)
        context = Context()
        for stmt in t.body:
            infer_func(stmt, context, solver)

        return context

    def is_builtin(self, module_name):
        raise NotImplementedError("Not implemented yet")
