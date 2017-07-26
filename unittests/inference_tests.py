import builtins
import glob
import os
import unittest

import time
from frontend.stmt_inferrer import *


class TestInference(unittest.TestCase):
    def __init__(self, file_path, file_name):
        super().__init__()
        self.file_path = file_path
        self.file_name = file_name
        self.sat = True
        self.throws = None
        self.ignore = False

    @staticmethod
    def parse_comment(comment):
        assignment_text = comment[2:]  # remove the '# ' text
        variable, type_annotation = assignment_text.split(" := ")
        return variable, type_annotation

    def parse_results(self, source):
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
            if line[2:8] == "throws":
                self.throws = line[9:]
                continue
            variable, t = self.parse_comment(line)
            result[variable] = t
        return result

    @staticmethod
    def infer_file(path):
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

        return solver, context

    def runTest(self):
        """Test for expressions inference"""
        start_time = time.time()
        r = open(self.file_path)
        expected_result = self.parse_results(r)
        r.close()

        if self.ignore:
            return

        if self.throws:
            self.assertRaises(getattr(builtins, self.throws), self.infer_file, self.file_path)
            end_time = time.time()
            print(self.test_end_message(end_time - start_time))
            return

        solver, context = self.infer_file(self.file_path)

        check = solver.optimize.check()
        if self.sat:
            self.assertNotEqual(check, z3_types.unsat)
        else:
            self.assertEqual(check, z3_types.unsat)
            end_time = time.time()
            print(self.test_end_message(end_time - start_time))
            return

        model = solver.optimize.model()
        for v in expected_result:
            self.assertTrue(context.has_var_in_children(v),
                            "Test file {}. Expected to have variable '{}' in the program".format(self.file_name, v))

            z3_type = context.get_var_from_children(v)
            expected = solver.annotation_resolver.resolve(ast.parse(expected_result[v]).body[0].value, solver)
            self.assertEqual(model[z3_type], expected,
                             "Test file {}. Expected variable '{}' to have type '{}', but found '{}'"
                             .format(self.file_name, v, expected, model[z3_type]))
        end_time = time.time()
        print(self.test_end_message(end_time - start_time))

    def test_end_message(self, duration):
        return "Tested {} in {:.2f} seconds.".format(self.file_name, duration)


def suite():
    s = unittest.TestSuite()
    g = os.getcwd() + '/unittests/inference/**.py'
    for path in glob.iglob(g):
        if os.path.basename(path) != "__init__.py":
            name = path.split("/")[-1]
            s.addTest(TestInference(path, name))
    runner = unittest.TextTestRunner(verbosity=0)
    runner.run(s)


if __name__ == '__main__':
    suite()
