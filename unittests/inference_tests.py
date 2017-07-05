import glob
import os
import unittest
from frontend.stmt_inferrer import *


class TestInference(unittest.TestCase):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    @staticmethod
    def parse_comment(comment):
        assignment_text = comment[2:]  # remove the '# ' text
        variable, type_annotation = assignment_text.split(" := ")
        return variable, type_annotation

    @classmethod
    def parse_results(cls, source, solver):
        result = {}
        for line in source:
            line = line.strip()
            if not line.startswith("#"):
                continue
            variable, t = cls.parse_comment(line)
            result[variable] = solver.resolve_annotation(ast.parse(t).body[0].value)
        return result

    @classmethod
    def infer_file(cls, path):
        """Infer a single python program

        :param path: file system path of the program to infer 
        :return: the z3 solver used to infer the program, and the global context of the program
        """
        r = open(path)
        t = ast.parse(r.read())
        r.close()

        solver = z3_types.TypesSolver(t)

        context = Context()

        solver.infer_stubs(context, infer)

        for stmt in t.body:
            infer(stmt, context, solver)

        solver.push()

        r = open(path)
        expected_result = cls.parse_results(r, solver)
        r.close()

        return solver, context, expected_result

    def runTest(self):
        """Test for expressions inference"""
        solver, context, expected_result = self.infer_file(self.file_path)

        check = solver.optimize.check()
        self.assertNotEqual(check, z3_types.unsat)

        model = solver.optimize.model()
        for v in expected_result:
            self.assertIn(v, context.types_map,
                          "Expected to have variable '{}' in the global context".format(v))

            z3_type = context.types_map[v]
            self.assertEqual(model[z3_type], expected_result[v],
                             "Expected variable '{}' to have type '{}', but found '{}'".format(v,
                                                                                               expected_result[v],
                                                                                               model[z3_type]))


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/unittests/inference/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            s.addTest(TestInference(path))
    runner = unittest.TextTestRunner()
    runner.run(s)

if __name__ == '__main__':
    suite()
