import ast
from frontend.context import Context
from frontend.stubs.stubs_paths import libraries


class ImportHandler:
    """Handler for importing other modules during the type inference"""
    cached_asts = {}
    already_inferred = {}

    @staticmethod
    def get_ast(base_folders, module_name):
        """Get the AST of a python module
        
        :param path: the path to the python module
        :param module_name: the name of the python module
        """
        if module_name in ImportHandler.cached_asts:
            return ImportHandler.cached_asts[module_name]
        for base in base_folders:
            path_direct = base + '/' + module_name.replace('.', '/') + '.pyi'
            path_init = base + '/' + module_name.replace('.', '/') + '/__init__.pyi'
            try:
                r = open(path_direct)
                break
            except Exception:
                try:
                    r = open(path_init)
                    break
                except Exception:
                    continue
        else:
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
        return ImportHandler.get_ast(base_folder, module_name)

    @staticmethod
    def get_builtin_ast(module_name):
        """Return the AST of a built-in module"""
        return ImportHandler.get_ast(libraries[module_name], module_name)

    @staticmethod
    def infer_import(module_name, base_folder, infer_func, solver):
        if module_name in ImportHandler.already_inferred:
            return ImportHandler.already_inferred[module_name]
        print(module_name)
        """Infer the types of a python module"""
        if ImportHandler.is_builtin(module_name):
            return solver.stubs_handler.infer_builtin_lib(module_name, solver,
                                                          solver.config.used_names, infer_func)
        else:
            t = ImportHandler.get_module_ast(module_name, base_folder)
            context = Context(t.body, solver)
            solver.infer_stubs(context, infer_func)
            for stmt in t.body:
                infer_func(stmt, context, solver)
        ImportHandler.already_inferred[module_name] = context
        return context

    @staticmethod
    def is_builtin(module_name):
        """Check if the imported python module is builtin"""
        return module_name in libraries
