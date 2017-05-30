import ast
from frontend.context import Context


class ImportHandler:
    """Handler for importing other modules during the type inference"""
    @staticmethod
    def get_ast(module_name, base_folder):
        """Get the AST of a python module
        
        :param module_name: the name of the python module
        :param base_folder: the directory path where this module exists
        """
        r = open("{}/{}.py".format(base_folder, module_name))
        return ast.parse(r.read())

    @staticmethod
    def infer_import(module_name, base_folder, infer_func, solver):
        """Infer the types of a python module"""
        if ImportHandler.is_builtin(module_name):
            # TODO import from builtins
            pass

        t = ImportHandler.get_ast(module_name, base_folder)
        context = Context()
        for stmt in t.body:
            infer_func(stmt, context, solver)

        return context

    @staticmethod
    def is_builtin(module_name):
        """Check if the imported python module is builtin"""
        # TODO
        pass
