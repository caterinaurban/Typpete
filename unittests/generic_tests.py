import ast
import io
import logging
import os
import re
import string
import sys
import tokenize
import unittest
from abc import abstractmethod

from core.expressions import VariableIdentifier
from engine.forward import ForwardInterpreter
from frontend.cfg_generator import ast_to_cfg
from semantics.forward import DefaultForwardSemantics
from unittests.test_lattices import ExpressionStore
from visualization.graph_renderer import CfgRenderer, AnalysisResultRenderer


def format_filename(s):
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.

    """
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    # filename = filename.replace(' ', '_')  # I don't like spaces in filenames.

    return filename


def source_path_to_name(source_path):
    return os.path.splitext(os.path.basename(source_path))[0]


class SourceTestCase(unittest.TestCase):
    def __init__(self, name=None, source=None):
        super().__init__()
        self._source = source
        self._cfg = None
        self._ast_root = None
        self._name = format_filename(name or source)

    def setUp(self):
        self._ast_root = ast.parse(self.source)
        self._cfg = ast_to_cfg(self.ast_root)
        super().setUp()

    def render_cfg(self):
        CfgRenderer().render(self.cfg, label=f"CFG for {self.name}", filename=f"CFG {self.name}",
                             directory=os.path.join(self.get_graphs_directory(), "graphs"),
                             view=False)

    def render_result_cfg(self, result):
        AnalysisResultRenderer().render((self.cfg, result), label=f"CFG with Results for {self.name}",
                                        filename=f"CFGR {self.name}",
                                        directory=os.path.join(self.get_graphs_directory(), "graphs"), view=False)

    def find_variable_names(self):
        """Finds the names of all variables in the source."""
        return sorted(
            {node.id for node in ast.walk(self.ast_root) if
             isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)})

    def get_graphs_directory(self):
        return "./"

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source

    @property
    def cfg(self):
        return self._cfg

    @property
    def ast_root(self):
        return self._ast_root

    def __str__(self):
        return f"Unit test for {self._name}"


class FileTestCase(SourceTestCase):
    def __init__(self, source_path):
        super().__init__(name=source_path_to_name(source_path))
        self._source_path = source_path
        self._source_directory = os.path.dirname(self._source_path)

    def setUp(self):
        with open(self._source_path, 'r') as source_file:
            self._source = source_file.read()
        super().setUp()

    @property
    def source_path(self):
        return self._source_path

    @abstractmethod
    def runTest(self):
        """
        Specific test logic.
        """

    def get_graphs_directory(self):
        return self._source_directory

    def __str__(self):
        return f"Unit test for Python source at {self._source_path}"


class ResultCommentsFileTestCase(FileTestCase):
    def __init__(self, source_path):
        super().__init__(source_path)

    @abstractmethod
    def runTest(self):
        """
        Specific test logic.
        """

    def check_result_comments(self, result):
        result_comments = list(self._find_result_comments())
        for line, expected_result in result_comments:
            actual_result = self._find_analysis_result_for_comments(result, line, expected_result)
            actual_result_str = str(actual_result)
            self.assertEqual(expected_result, actual_result_str,
                             f"expected != actual result at line {line}")
        logging.info(f"\t{len(result_comments)} expected result(s) checked")

    def _find_result_comments(self):
        # Parse comments to find expected results
        pattern = re.compile('RESULT:?\s*(?P<result>.*)')
        for t in tokenize.tokenize(io.BytesIO(self.source.encode('utf-8')).readline):
            if t.type == tokenize.COMMENT:
                comment = t.string.strip("# ")
                m = pattern.match(comment)
                if m:
                    expected_result = m.group('result')
                    line = t.start[0]
                    yield line, expected_result

    def _find_analysis_result_for_comments(self, result, line_of_comment, expected_result):
        """
        Search for closest succeeding analysis result after the line of the comment.
        
        NOTE: If the result was produced by a forward/backwards analysis is **not** important.
        """
        actual_result = None
        least_distance = sys.maxsize
        for node in self.cfg.nodes.values():
            states = result.get_node_result(node)

            for i, stmt in enumerate(node.stmts):
                d = stmt.pp.line - line_of_comment
                if 0 < d < least_distance:
                    actual_result = states[i]
                    least_distance = d

            # special treatment for expected result comments after last statement of a block but before any other
            # statement of succeeding (= larger start line number) block
            if node.stmts:
                d = line_of_comment - node.stmts[-1].pp.line
                if 0 <= d < least_distance:
                    actual_result = states[-1]
                    least_distance = d

        if actual_result:
            return actual_result
        else:
            raise RuntimeError(
                f"No analysis result found for RESULT-comment '{expected_result}' at line {line_of_comment}!")


class ExpressionTreeTestCase(SourceTestCase):
    def __init__(self, source, name=None):
        self.variables = {}
        super().__init__(name=format_filename(name or source), source=source)

    def runTest(self):
        variable_names = self.find_variable_names()
        for name in variable_names:
            # TODO remove this name hack when type inferences work
            typ = list if name.startswith("list") else int
            self.variables[name] = VariableIdentifier(typ, name)

        forward_interpreter = ForwardInterpreter(self.cfg, DefaultForwardSemantics(), 3)
        result = forward_interpreter.analyze(ExpressionStore(list(self.variables.values())))

        self.render_result_cfg(result)

        return result
