import io
import tokenize
import os
import re
import unittest
from abc import abstractmethod
import ast

import sys

from frontend.cfg_generator import ast_to_cfg
from visualization.graph_renderer import CfgRenderer, AnalysisResultRenderer
import logging


def source_path_to_name(source_path):
    return os.path.splitext(os.path.basename(source_path))[0]


class FileTestCase(unittest.TestCase):
    def __init__(self, source_path):
        super().__init__()
        self._source_path = source_path
        self._source_directory = os.path.dirname(self._source_path)
        self._name = source_path_to_name(self._source_path)

    def setUp(self):
        with open(self._source_path, 'r') as source_file:
            self._source = source_file.read()
        self._ast_root = ast.parse(self.source)
        self._cfg = ast_to_cfg(self.ast_root)

    def render_cfg(self):
        CfgRenderer().render(self.cfg, label=f"CFG for {self.source_path}", filename=f"CFG {self.name}",
                             directory=os.path.join(self._source_directory, "graphs"),
                             view=False)

    def render_result_cfg(self, result):
        AnalysisResultRenderer().render((self.cfg, result), label=f"CFG with Results for {self._source_path}",
                                        filename=f"CFGR {self.name}",
                                        directory=os.path.join(self._source_directory, "graphs"), view=False)

    @property
    def source_path(self):
        return self._source_path

    @property
    def name(self):
        return self._name

    @property
    def ast_root(self):
        return self._ast_root

    @property
    def source(self):
        return self._source

    @property
    def cfg(self):
        return self._cfg

    @abstractmethod
    def runTest(self):
        """
        Specific test logic.
        """

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
        Search for closest succeeding analysis result after the line of the comment
        """
        actual_result = None
        actual_result_line = sys.maxsize
        for node in self.cfg.nodes.values():
            states = result.get_node_result(node)

            for i, stmt in enumerate(node.stmts):
                if line_of_comment < stmt.pp.line < actual_result_line:
                    actual_result = states[i]
                    actual_result_line = stmt.pp.line

            # special treatment for expected result comments after last statement of a block but before any other
            # statement of succeeding (= larger start line number) block
            if node.stmts and node.stmts[-1].pp.line < line_of_comment < actual_result_line:
                actual_result = states[-1]  # take last result in block as actual result
                actual_result_line = line_of_comment

        if actual_result:
            return actual_result
        else:
            raise RuntimeError(
                f"No analysis result found for RESULT-comment '{expected_result}' at line {line_of_comment}!")
