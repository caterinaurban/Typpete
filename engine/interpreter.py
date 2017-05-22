from abc import abstractmethod, ABCMeta
from abstract_domains.state import State
from core.cfg import ControlFlowGraph
from engine.result import AnalysisResult
from semantics.semantics import Semantics


class Interpreter(metaclass=ABCMeta):
    def __init__(self, cfg: ControlFlowGraph, semantics: Semantics, widening: int):
        """Analysis runner.
        
        :param cfg: control flow graph to analyze
        :param widening: number of iterations before widening 
        """
        self._result = AnalysisResult(cfg)
        self._semantics = semantics
        self._widening = widening

    @property
    def result(self):
        return self._result

    @property
    def cfg(self):
        return self.result.cfg

    @property
    def semantics(self):
        return self._semantics

    @property
    def widening(self):
        return self._widening

    @abstractmethod
    def analyze(self, initial: State) -> AnalysisResult:
        """Run the analysis.
        
        :param initial: initial analysis state
        :return: result of the analysis
        """
