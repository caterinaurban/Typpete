from abc import ABC, abstractmethod
from cfg import ControlFlowGraph
from result import AnalysisResult
from state import State


class Interpreter(ABC):
    def __init__(self, cfg: ControlFlowGraph, widening: int):
        """Analysis runner.
        
        :param cfg: control flow graph to analyze
        :param widening: number of iterations before widening 
        """
        self._result = AnalysisResult(cfg)
        self._widening = widening

    @property
    def result(self):
        return self._result

    @property
    def cfg(self):
        return self.result.cfg

    @property
    def widening(self):
        return self._widening

    @abstractmethod
    def analyze(self, initial: State) -> AnalysisResult:
        """Run the analysis.
        
        :param initial: initial analysis state
        :return: result of the analysis
        """
