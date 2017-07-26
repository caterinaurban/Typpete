from collections import OrderedDict
from frontend.import_handler import ImportHandler
import ast


class PreAnalyzer:
    """Analyzer for the AST, It provides the following configurations before the type inference:
        - The maximum args length of functions in the whole program
        - The maximum tuple length in the whole program
        - All the used names (variables, functions, classes, etc.) in the program,
            to be used in inferring relevant stub functions.
        - Class and instance attributes
    """

    def __init__(self, prog_ast, base_folder):
        """
        :param prog_ast: The AST for the python program  
        """
        # List all the nodes existing in the AST
        self.base_folder = base_folder
        self.all_nodes = self.walk(prog_ast)
        self.stub_nodes = []

    def walk(self, prog_ast):
        result = list(ast.walk(prog_ast))
        import_nodes = [node for node in result if isinstance(node, ast.Import)]
        import_from_nodes = [node for node in result if isinstance(node, ast.ImportFrom)]
        for node in import_nodes:
            for name in node.names:
                if ImportHandler.is_builtin(name.name):
                    # No need to analyze built-in library modules, all functions are stubs
                    continue
                new_ast = ImportHandler.get_ast(name.name, self.base_folder)
                result += self.walk(new_ast)
        for node in import_from_nodes:
            if ImportHandler.is_builtin(node.module):
                # No need to analyze built-in library modules, all functions are stubs
                continue
            if node.module == "typing":
                # FIXME ignore typing for now, not to break type vars
                continue
            new_ast = ImportHandler.get_ast(node.module, self.base_folder)
            result += self.walk(new_ast)

        return result

    def add_stub_ast(self, tree):
        """Add an AST of a stub file to the pre-analyzer"""
        self.stub_nodes += list(ast.walk(tree))

    def maximum_function_args(self):
        """Get the maximum number of function arguments appearing in the AST"""
        user_func_defs = [node for node in self.all_nodes if isinstance(node, ast.FunctionDef)]
        stub_func_defs = [node for node in self.stub_nodes if isinstance(node, ast.FunctionDef)]

        # A minimum value of 1 because a default __init__ with one argument function
        # is added to classes that doesn't contain one
        user_func_max = max([len(node.args.args) for node in user_func_defs] + [1])
        stub_func_max = max([len(node.args.args) for node in stub_func_defs] + [1])

        return max(user_func_max, stub_func_max)

    def max_default_args(self):
        """Get the maximum number of default arguments appearing in all function definitions"""
        func_defs = [node for node in self.all_nodes if isinstance(node, ast.FunctionDef)]
        return max([len(node.args.defaults) for node in func_defs] + [0])

    def maximum_tuple_length(self):
        """Get the maximum length of tuples appearing in the AST"""
        user_tuples = [node for node in self.all_nodes if isinstance(node, ast.Tuple)]
        stub_tuples = [node for node in self.stub_nodes if isinstance(node, ast.Tuple)]

        user_max = max([len(node.elts) for node in user_tuples] + [0])
        stub_tuples = max([len(node.elts) for node in stub_tuples] + [0])

        return max(user_max, stub_tuples)

    def get_all_used_names(self):
        """Get all used variable names and used-defined classes names"""
        names = [node.id for node in self.all_nodes if isinstance(node, ast.Name)]
        names += [node.name for node in self.all_nodes if isinstance(node, ast.ClassDef)]
        names += [node.attr for node in self.all_nodes if isinstance(node, ast.Attribute)]
        names += [node.name for node in self.all_nodes if isinstance(node, ast.alias)]
        return names

    def analyze_classes(self):
        """Pre-analyze and configure classes before the type inference
        
        Do the following:
            - Propagate methods from bases to subclasses.
            - Add __init__ function to classes if it doesn't exist.
            - Return a mapping from class names to their attributes and methods.
            - Return a mapping from class names to their base classes if they have any.
            
        """
        # TODO propagate attributes to subclasses.
        class_defs = [node for node in self.all_nodes if isinstance(node, ast.ClassDef)]

        propagate_attributes_to_subclasses(class_defs)

        class_to_instance_attributes = OrderedDict()
        class_to_class_attributes = OrderedDict()
        class_to_base = OrderedDict()

        for cls in class_defs:
            if len(cls.bases) > 1:
                raise NotImplementedError("Multiple inheritance is not supported yet.")
            elif cls.bases:
                class_to_base[cls.name] = cls.bases[0].id
            else:
                class_to_base[cls.name] = "object"

            add_init_if_not_existing(cls)

            # instance attributes contains all attributes that can be accessed through the instance
            instance_attributes = set()

            # class attributes contains all attributes that can be accessed through the class
            # Ex:
            # class A:
            #     x = 1
            # A.x

            # class attributes are subset from instance attributes
            class_attributes = set()
            class_to_instance_attributes[cls.name] = instance_attributes
            class_to_class_attributes[cls.name] = class_attributes

            # Inspect all class-level statements
            for cls_stmt in cls.body:
                if isinstance(cls_stmt, ast.FunctionDef):
                    # Add function to class attributes and get attributes defined by self.some_attribute = value
                    instance_attributes.add(cls_stmt.name)
                    class_attributes.add(cls_stmt.name)
                    if not cls_stmt.args.args:
                        continue
                    first_arg = cls_stmt.args.args[0].arg  # In most cases it will be 'self'

                    # Get attribute assignments where attribute value is the same as the first argument
                    func_nodes = ast.walk(cls_stmt)
                    assignments = [node for node in func_nodes if isinstance(node, ast.Assign)]

                    for assignment in assignments:
                        for target in assignment.targets:
                            if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and
                                    target.value.id == first_arg):
                                instance_attributes.add(target.attr)
                elif isinstance(cls_stmt, ast.Assign):
                    # Get attributes defined as class-level assignment
                    for target in cls_stmt.targets:
                        if isinstance(target, ast.Name):
                            class_attributes.add(target.id)
                            instance_attributes.add(target.id)

        return class_to_instance_attributes, class_to_class_attributes, class_to_base

    def get_all_configurations(self):
        config = Configuration()
        config.max_tuple_length = self.maximum_tuple_length()
        config.max_function_args = self.maximum_function_args()
        config.base_folder = self.base_folder
        config.classes_to_instance_attrs, config.classes_to_class_attrs, config.class_to_base = self.analyze_classes()
        config.used_names = self.get_all_used_names()
        config.max_default_args = self.max_default_args()

        return config


class Configuration:
    """A class holding configurations given by the pre-analyzer"""
    def __init__(self):
        self.max_tuple_length = 0
        self.max_function_args = 1
        self.classes_to_attrs = OrderedDict()
        self.class_to_base = OrderedDict()
        self.base_folder = ""
        self.used_names = []
        self.max_default_args = 0


def propagate_attributes_to_subclasses(class_defs):
    """Start depth-first methods propagation from inheritance roots to subclasses"""
    inheritance_forest = get_inheritance_forest(class_defs)
    roots = get_forest_roots(inheritance_forest)
    name_to_node = class_name_to_node(class_defs)

    for root in roots:
        propagate(root, inheritance_forest, name_to_node)


def propagate(node, inheritance_forest, name_to_node):
    """Propagate methods to subclasses with depth first manner.
    
    :param node: The class node whose methods are to be propagated
    :param inheritance_forest: A data-structure containing the inheritance hierarchy
    :param name_to_node: A mapping from class names to their AST nodes 
    """
    for subclass in inheritance_forest[node]:
        base_node = name_to_node[node]
        sub_node = name_to_node[subclass]
        sub_funcs_names = [func.name for func in sub_node.body if isinstance(func, ast.FunctionDef)]

        # Select only functions that are not overridden in the subclasses.
        inherited_funcs = [func for func in base_node.body
                           if isinstance(func, ast.FunctionDef) and func.name not in sub_funcs_names]
        sub_node.body += inherited_funcs
        # Propagate to sub-subclasses..
        propagate(subclass, inheritance_forest, name_to_node)


def class_name_to_node(nodes):
    """Return a mapping for the class name to its AST node."""
    name_to_node = {}
    for node in nodes:
        name_to_node[node.name] = node
    return name_to_node


def get_forest_roots(forest):
    """Return list of classes that have no super-class (other than object)"""
    roots = list(forest.keys())
    for node in forest:
        for sub in forest[node]:
            if sub in roots:
                roots.remove(sub)
    return roots


def get_inheritance_forest(class_defs):
    """Return a forest of class nodes
    
    Each tree represents an inheritance hierarchy. There is a directed edge between class 'a' and class 'b'
    if 'b' extends 'a'.
    """
    tree = {}
    for cls in class_defs:
        tree[cls.name] = []
    for cls in class_defs:
        bases = cls.bases
        for base in bases:
            tree[base.id].append(cls.name)
    return tree


def add_init_if_not_existing(class_node):
    """Add a default empty __init__ function if it doesn't exist in the class node"""
    for stmt in class_node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
            return
    class_node.body.append(ast.FunctionDef(
        name="__init__",
        args=ast.arguments(args=[ast.arg(arg="self", annotation=None)]),
        body=[ast.Pass()],
        decorator_list=[],
        returns=None,
        lineno=class_node.lineno
    ))
