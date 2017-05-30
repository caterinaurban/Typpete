import ast
from frontend.context import Context
from frontend.z3_types import TypesSolver, unsat
from frontend.pre_analysis import PreAnalyzer


class ImportHandler:
    def infer_import_from(self, module_name, relative_level, names):
        if not relative_level and self.is_builtin(module_name):
            # TODO import builtins
            pass
        # TODO

    @staticmethod
    def infer_import(module_name, base_folder, infer_func):
        r = open("{}/{}.py".format(base_folder, module_name))
        t = ast.parse(r.read())
        pre_analyzer = PreAnalyzer(t)
        solver = TypesSolver(pre_analyzer.get_all_configurations())
        context = Context()
        for stmt in t.body:
            infer_func(stmt, context, solver)

        solver.push()
        if solver.check(solver.assertions_vars) == unsat:
            raise TypesSolver("The imported module {} is not type correct".format(module_name))
        model = solver.model()
        result = {}
        for v in context.types_map:
            result[v] = model[context.types_map[v]]

        result_context = Context()
        result_context.types_map = result
        return result_context, solver.z3_types.all_types, solver.z3_types.attributes

    def is_builtin(self, module_name):
        raise NotImplementedError("Not implemented yet")
