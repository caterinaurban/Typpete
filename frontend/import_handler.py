import ast
from frontend.context import Context
from frontend.stubs.stubs_paths import libraries


class ImportHandler:
    """Handler for importing other modules during the type inference"""
    cached_asts = {}
    cached_modules = {}

    @staticmethod
    def get_ast(path, module_name):
        """Get the AST of a python module
        
        :param path: the path to the python module
        :param module_name: the name of the python module
        """
        if module_name in ImportHandler.cached_asts:
            return ImportHandler.cached_asts[module_name]
        try:
            r = open(path)
        except FileNotFoundError:
            raise ImportError("No module named {}.".format(module_name))

        tree = ast.parse(r.read())
        r.close()
        ImportHandler.cached_asts[module_name] = tree
        return tree

    @staticmethod
    def get_module_ast(module_name, base_folder):
        """Get the AST of a python module

        :param module_name: the name of the python module
        :param base_folder: the base folder containing the python module
        """
        return ImportHandler.get_ast("{}/{}.py".format(base_folder, module_name), module_name)

    @staticmethod
    def get_builtin_ast(module_name):
        """Return the AST of a built-in module"""
        return ImportHandler.get_ast(libraries[module_name], module_name)

    @staticmethod
    def infer_import(module_name, base_folder, infer_func, solver):
        """Infer the types of a python module"""
        if module_name in ImportHandler.cached_modules:
            # Return the cached context if this module is already inferred before
            return ImportHandler.cached_modules[module_name]
        if ImportHandler.is_builtin(module_name):
            ImportHandler.cached_modules[module_name] = solver.stubs_handler.infer_builtin_lib(module_name,
                                                                                               solver,
                                                                                               solver.config.used_names,
                                                                                                           infer_func)
        else:
            t = ImportHandler.get_module_ast(module_name, base_folder)
            context = Context(t.body, solver)
            solver.infer_stubs(context, infer_func)
            for stmt in t.body:
                infer_func(stmt, context, solver)
            ImportHandler.cached_modules[module_name] = context
        return ImportHandler.cached_modules[module_name]

    @staticmethod
    def is_builtin(module_name):
        """Check if the imported python module is builtin"""
        return module_name in libraries
