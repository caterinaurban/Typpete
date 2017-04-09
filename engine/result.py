from cfg import ControlFlowGraph
from itertools import zip_longest
from state import State
from typing import List


class AnalysisResult(object):
    def __init__(self, cfg: ControlFlowGraph):
        """Analysis result representation.
        
        :param cfg: analyzed control flow graph
        """
        self._cfg = cfg
        self._result = dict()

    @property
    def cfg(self):
        return self._cfg

    @property
    def result(self):
        return self._result

    def get_block_result(self, identifier: int) -> List[State]:
        """Get the analysis result for a block.
        
        :param identifier: identifier of the analyzed block
        :return: list of states representing the result of the analysis for the block
        """
        return self.result[identifier]

    def set_block_result(self, identifier: int, states: List[State]) -> None:
        """Set the analysis result for a block.
        
        :param identifier: identifier of the analyzed block
        :param states: list of states representing the result of the analysis for the block
        """
        self.result[identifier] = states

    def __str__(self):
        """Analysis result string representation.
        
        :return: string representing the result of the analysis
        """
        result = []
        for identifier in self.cfg.nodes:
            node = self.cfg.nodes[identifier]
            result.append("********* {} *********".format(node))
            states = self.get_block_result(identifier)
            block = [elm for pair in zip_longest(states, node.stmts) for elm in pair if elm is not None]
            result.append("\n".join("{}".format(elm) for elm in block))
        return "\n".join(res for res in result)
