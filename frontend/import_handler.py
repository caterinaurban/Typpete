import ast
from frontend.context import Context
from frontend.stubs.stubs_paths import libraries


class ImportHandler:
    """Handler for importing other modules during the type inference"""

    @staticmethod
    def get_ast(module_name, base_folder):
        """Get the AST of a python module
        
        :param module_name: the name of the python module
        :param base_folder: the directory path where this module exists
        """
        try:
            r = open("{}/{}.py".format(base_folder, module_name))
        except FileNotFoundError:
            raise ImportError("No module named {}.".format(module_name))

        tree = ast.parse(r.read())
        r.close()
        return tree

    @staticmethod
    def infer_import(module_name, base_folder, infer_func, solver):
        """Infer the types of a python module"""
        context = Context()

        if ImportHandler.is_builtin(module_name):
            solver.stubs_handler.infer_builtin_lib(module_name, context, solver,
                                                   solver.config.used_names, infer_func)
        else:
            t = ImportHandler.get_ast(module_name, base_folder)
            solver.infer_stubs(context, infer_func)
            for stmt in t.body:
                infer_func(stmt, context, solver)

        return context

    @staticmethod
    def is_builtin(module_name):
        """Check if the imported python module is builtin"""
        return module_name in libraries
