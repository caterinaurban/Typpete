import ast


class PreAnalyzer:
    def __init__(self, prog_ast):
        self.all_nodes = ast.walk(prog_ast)

    def maximum_function_args(self):
        func_defs = [node for node in self.all_nodes if isinstance(node, ast.FunctionDef)]
        return 0 if len(func_defs) == 0 else max([len(node.args.args) for node in func_defs])

    def maximum_tuple_length(self):
        tuples = [node for node in self.all_nodes if isinstance(node, ast.Tuple)]
        return 0 if len(tuples) == 0 else max([len(node.elts) for node in tuples])
