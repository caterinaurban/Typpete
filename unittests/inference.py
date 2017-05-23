import unittest
from frontend.pre_analysis import PreAnalyzer
from frontend.stmt_inferrer import *


class TestInference(unittest.TestCase):
    @staticmethod
    def infer_file(path):
        """Infer a single python program
        
        :param path: file system path of the program to infer 
        :return: the z3 solver used to infer the program, and the global context of the program
        """
        r = open(path)
        t = ast.parse(r.read())

        analyzer = PreAnalyzer(t)

        config = analyzer.get_all_configurations()
        solver = z3_types.TypesSolver(config)

        context = Context()
        for stmt in t.body:
            infer(stmt, context, solver)

        solver.push()
        return solver, context

    def test_classes(self):
        """Test for class definitions, instantiation and attribute access inference"""
        solver, context = self.infer_file("tests/inference/classes_test.py")
        type_sort = solver.z3_types.type_sort

        self.assertNotEqual(solver.check(solver.assertions_vars), z3_types.unsat)

        model = solver.model()
        class_a = context.types_map["A"]
        class_b = context.types_map["B"]
        class_c = context.types_map["C"]
        class_d = context.types_map["D"]
        class_e = context.types_map["E"]
        func_fab = context.types_map["fab"]
        var_x = context.types_map["x"]
        var_c = context.types_map["c"]
        var_e = context.types_map["e"]

        self.assertEqual(model[class_a], type_sort.type_type(type_sort.class_A))
        self.assertEqual(model[class_b], type_sort.type_type(type_sort.class_B))
        self.assertEqual(model[class_c], type_sort.type_type(type_sort.class_C))
        self.assertEqual(model[class_d], type_sort.type_type(type_sort.class_D))
        self.assertEqual(model[class_e], type_sort.type_type(type_sort.class_E))
        self.assertEqual(model[func_fab], type_sort.func_1(type_sort.type_type(type_sort.class_B),
                                                           type_sort.str))
        self.assertEqual(model[var_x], type_sort.str)
        self.assertEqual(model[var_c], type_sort.class_C)
        self.assertEqual(model[var_e], type_sort.class_E)

    def test_expressions(self):
        """Test for expressions inference"""
        solver, context = self.infer_file("tests/inference/expressions_test.py")
        types = solver.z3_types

        self.assertNotEqual(solver.check(solver.assertions_vars), z3_types.unsat)

        model = solver.model()
        var_a = context.types_map["a"]
        var_b = context.types_map["b"]
        var_c = context.types_map["c"]
        var_d = context.types_map["d"]
        var_f = context.types_map["f"]
        var_i = context.types_map["i"]
        var_o = context.types_map["o"]
        var_t = context.types_map["t"]
        var_u = context.types_map["u"]
        var_v = context.types_map["v"]
        var_w = context.types_map["w"]

        self.assertEqual(model[var_a], types.float)
        self.assertEqual(model[var_b], types.float)
        self.assertEqual(model[var_c], types.list(types.float))
        self.assertEqual(model[var_d], types.list(types.list(types.float)))
        self.assertEqual(model[var_f], types.int)
        self.assertEqual(model[var_i], types.dict(types.int, types.float))
        self.assertEqual(model[var_o], types.int)
        self.assertEqual(model[var_t], types.list(types.int))
        self.assertEqual(model[var_u], types.int)
        self.assertEqual(model[var_v], types.int)
        self.assertEqual(model[var_w], types.list(types.int))

    def test_functions(self):
        """Test for function definitions and calls inference"""
        solver, context = self.infer_file("tests/inference/functions_test.py")
        types = solver.z3_types

        self.assertNotEqual(solver.check(solver.assertions_vars), z3_types.unsat)

        model = solver.model()
        var_a = context.types_map["a"]
        var_b = context.types_map["b"]
        var_c = context.types_map["c"]
        func_f1 = context.types_map["f1"]
        func_f2 = context.types_map["f2"]
        func_f3 = context.types_map["f3"]
        func_f4 = context.types_map["f4"]
        func_f5 = context.types_map["f5"]
        func_f6 = context.types_map["f6"]

        self.assertEqual(model[var_a], types.list(types.int))
        self.assertEqual(model[var_b], types.list(types.int))
        self.assertEqual(model[var_c], types.list(types.int))
        self.assertEqual(model[func_f1], types.funcs[1](types.list(types.int),
                                                        types.list(types.int)))
        self.assertEqual(model[func_f2], types.funcs[1](types.int,
                                                        types.list(types.int)))
        self.assertEqual(model[func_f3], types.funcs[1](types.list(types.int),
                                                        types.list(types.int)))
        self.assertEqual(model[func_f4], types.funcs[2](types.dict(types.string, types.int),
                                                        types.int,
                                                        types.int))
        self.assertEqual(model[func_f5], types.funcs[3](types.list(types.int),
                                                        types.dict(types.string, types.int),
                                                        types.int,
                                                        types.int))
        self.assertEqual(model[func_f6], types.funcs[1](types.dict(types.string, types.int),
                                                        types.int))

    def test_statements(self):
        """Test for statements inference"""
        solver, context = self.infer_file("tests/inference/statements_test.py")
        types = solver.z3_types

        self.assertNotEqual(solver.check(solver.assertions_vars), z3_types.unsat)

        model = solver.model()
        var_l1 = context.types_map["L1"]
        var_l2 = context.types_map["L2"]
        var_i = context.types_map["i"]
        var_j = context.types_map["j"]

        self.assertEqual(model[var_l1], types.list(types.int))
        self.assertEqual(model[var_l2], types.list(types.int))
        self.assertEqual(model[var_i], types.int)
        self.assertEqual(model[var_j], types.int)

if __name__ == '__main__':
    unittest.main()
