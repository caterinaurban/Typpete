import ast


class PreAnalyzer:
    """Analyzer for the AST to give some configurations before the type inference"""
    def __init__(self, prog_ast):
        """
        :param prog_ast: The AST for the python program  
        """

        # List all the nodes existing in the AST
        self.all_nodes = list(ast.walk(prog_ast))

    def maximum_function_args(self):
        """Get the maximum number of function arguments appearing in the AST"""
        func_defs = [node for node in self.all_nodes if isinstance(node, ast.FunctionDef)]
        return 0 if len(func_defs) == 0 else max([len(node.args.args) for node in func_defs])

    def maximum_tuple_length(self):
        """Get the maximum length of tuples appearing in the AST"""
        tuples = [node for node in self.all_nodes if isinstance(node, ast.Tuple)]
        return 0 if len(tuples) == 0 else max([len(node.elts) for node in tuples])
