import glob
import os
import unittest
from frontend.stmt_inferrer import *


def print_complete_solver(z3solver):
    pp = z3_types.z3printer._PP
    pp.max_lines = 4000
    pp.max_width = 120
    formatter = z3_types.z3printer._Formatter
    formatter.max_visited = 100000
    formatter.max_depth = 50
    formatter.max_args = 512
    out = sys.stdout
    pp(out, formatter(z3solver))


class TestInference(unittest.TestCase):
    def __init__(self, file_path, file_name):
        super().__init__()
        self.file_path = file_path
        self.file_name = file_name
        self.sat = True
        self.ignore = False

    @staticmethod
    def parse_comment(comment):
        assignment_text = comment[2:]  # remove the '# ' text
        variable, type_annotation = assignment_text.split(" := ")
        return variable, type_annotation

    def parse_results(self, source, solver):
        result = {}
        for line in source:
            line = line.strip()
            if not line.startswith("#"):
                continue
            if line[2:] == "unsat":
                self.sat = False
                continue
            if line[2:] == "ignore":
                self.ignore = True
                continue
            variable, t = self.parse_comment(line)
            result[variable] = solver.resolve_annotation(ast.parse(t).body[0].value)
        return result

    def infer_file(self, path):
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
        expected_result = self.parse_results(r, solver)
        r.close()

        return solver, context, expected_result

    def runTest(self):
        """Test for expressions inference"""
        solver, context, expected_result = self.infer_file(self.file_path)

        if self.ignore:
            return

        check = solver.optimize.check()
        if self.sat:
            self.assertNotEqual(check, z3_types.unsat)
        else:
            self.assertEqual(check, z3_types.unsat)
            return

        model = solver.optimize.model()
        for v in expected_result:
            self.assertTrue(context.has_var_in_children(v),
                            "Test file {}. Expected to have variable '{}' in the program".format(self.file_name, v))

            z3_type = context.get_var_from_children(v)
            self.assertEqual(model[z3_type], expected_result[v],
                             "Test file {}. Expected variable '{}' to have type '{}', but found '{}'"
                             .format(self.file_name, v, expected_result[v], model[z3_type]))


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/unittests/inference/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            name = path.split("/")[-1]
            s.addTest(TestInference(path, name))
    runner = unittest.TextTestRunner()
    runner.run(s)


if __name__ == '__main__':
    suite()
