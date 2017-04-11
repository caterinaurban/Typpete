from core.cfg import ControlFlowGraph
from engine.interpreter import Interpreter
from engine.result import AnalysisResult
from abstract_domains.state import State


class BackwardInterpreter(Interpreter):
    def __init__(self, cfg: ControlFlowGraph, widening: int):
        """Backward analysis runner.

        :param cfg: control flow graph to analyze
        :param widening: number of iterations before widening 
        """
        super().__init__(cfg, widening)

    def analyze(self, initial: State) -> AnalysisResult:
        pass
