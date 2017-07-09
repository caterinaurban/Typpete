import ast
import os
from abc import abstractmethod
from engine.result import AnalysisResult
from frontend.cfg_generator import ast_to_cfg
from visualization.graph_renderer import AnalysisResultRenderer


class Runner:
    """Analysis runner."""

    def __init__(self):
        self._path = None
        self._tree = None
        self._cfg = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @property
    def tree(self):
        return self._tree

    @tree.setter
    def tree(self, tree):
        self._tree = tree

    @property
    def cfg(self):
        return self._cfg

    @cfg.setter
    def cfg(self, cfg):
        self._cfg = cfg

    @abstractmethod
    def interpreter(self):
        """Control flow graph interpreter."""

    @abstractmethod
    def state(self):
        """Initial analysis state."""

    def main(self, path):
        self.path = path
        with open(self.path, 'r') as source:
            self.tree = ast.parse(source.read())
            self.cfg = ast_to_cfg(self.tree)
        self.run()

    def run(self) -> AnalysisResult:
        result = self.interpreter().analyze(self.state())
        self.render(result)
        return result

    def render(self, result):
        name = os.path.splitext(os.path.basename(self.path))[0]
        label = f"CFG with Analysis Result for {name}"
        directory = os.path.dirname(self.path)
        AnalysisResultRenderer().render((self.cfg, result), filename=name, label=label, directory=directory, view=True)
