import ast
import astunparse
import os

from frontend.context import Context
from frontend.stubs.stubs_paths import libraries
from frontend.stubs.stubs_handler import STUB_ASTS


class ImportHandler:
    """Handler for importing other modules during the type inference"""
    cached_asts = {}
    cached_modules = {}
    module_to_path = {}

    @staticmethod
    def get_ast(path, module_name):
        """Get the AST of a python module
        
        :param path: the path to the python module
        :param module_name: the name of the python module
        """
        if module_name in ImportHandler.cached_asts:
            return ImportHandler.cached_asts[module_name]
        if path in STUB_ASTS:
            return STUB_ASTS[path]
        try:
            r = open(path)
        except FileNotFoundError:
            raise ImportError("No module named {}.".format(module_name))
        ImportHandler.module_to_path[module_name] = path
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
        return ImportHandler.get_ast("{}/{}.py".format(base_folder, module_name.replace('.', '/')), module_name)

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
            context = Context(t, t.body, solver)
            ImportHandler.cached_modules[module_name] = context
            solver.infer_stubs(context, infer_func)
            for stmt in t.body:
                infer_func(stmt, context, solver)
        return ImportHandler.cached_modules[module_name]

    @staticmethod
    def is_builtin(module_name):
        """Check if the imported python module is builtin"""
        return module_name in libraries

    @staticmethod
    def write_to_files(model, solver):
        for module in ImportHandler.module_to_path:
            if ImportHandler.is_builtin(module) or module not in ImportHandler.cached_modules:
                continue
            module_path = ImportHandler.module_to_path[module]
            module_ast = ImportHandler.cached_asts[module]
            module_context = ImportHandler.cached_modules[module]
            module_context.generate_typed_ast(model, solver)

            write_path = "inference_output/" + module_path
            if not os.path.exists(os.path.dirname(write_path)):
                os.makedirs(os.path.dirname(write_path))
            file = open(write_path, 'w')
            file.write(astunparse.unparse(module_ast))
            file.close()

