import ast
import astunparse
import os
from typpete.src.context import Context
from typpete.src.stubs.stubs_paths import libraries
from typpete.src.stubs.stubs_handler import STUB_ASTS


class ImportHandler:
    """Handler for importing other modules during the type inference"""
    cached_asts = {}
    cached_modules = {}
    module_to_path = {}
    class_to_module = {
        'List': ('typing', 0),
        'Tuple': ('typing', 0),
        'Callable': ('typing', 0),
        'Set': ('typing', 0),
        'Dict': ('typing', 0),
        'Union': ('typing', 0),
        'TypeVar': ('typing', 0),
        'Type': ('typing', 0),
        'IO': ('typing', 0),
        'Pattern': ('typing', 0),
        'Match': ('typing', 0),
        'Sequence': ('typing', 0),
    }

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
        module_name = module_name.replace('.', '/')
        if not base_folder:
            return ImportHandler.get_ast(module_name + ".py", module_name)
        return ImportHandler.get_ast("{}/{}.py".format(base_folder, module_name), module_name)

    @staticmethod
    def get_builtin_ast(module_name):
        """Return the AST of a built-in module"""
        directory = os.path.dirname(__file__) + '/stubs/'
        return ImportHandler.get_ast(directory + libraries[module_name], module_name)

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

            class_names = [c.name for c in t.body if isinstance(c, ast.ClassDef)]
            for cls in class_names:
                ImportHandler.class_to_module[cls] = (module_name, 0)

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

            ImportHandler.add_required_imports(module, module_ast, module_context)

            write_path = "inference_output/" + module_path
            if not os.path.exists(os.path.dirname(write_path)):
                os.makedirs(os.path.dirname(write_path))
            file = open(write_path, 'w')
            file.write(astunparse.unparse(module_ast))
            file.close()

    @staticmethod
    def add_required_imports(module_name, module_ast, module_context):
        imports = module_context.get_imports()

        if has_type_var(module_ast):
            imports.add('TypeVar')

        module_to_names = {}
        for imp in imports:
            if imp not in ImportHandler.class_to_module:
                continue
            mod = ImportHandler.class_to_module[imp]
            if mod in module_to_names:
                module_to_names[mod].append(imp)
            else:
                module_to_names[mod] = [imp]

        for (mod, level), names in module_to_names.items():
            if mod == module_name:
                continue
            aliases = [ast.alias(name=name, asname=None) for name in names]
            module_ast.body.insert(0, ast.ImportFrom(
                module=mod,
                names=aliases,
                level=level
            ))

def has_type_var(tree):
    return any(node.value.func.id for node in tree.body if
             isinstance(node, ast.Assign) and
             isinstance(node.value, ast.Call) and
             isinstance(node.value.func, ast.Name) and
             node.value.func.id == 'TypeVar')

