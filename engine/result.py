from core.cfg import Node, ControlFlowGraph
from itertools import zip_longest
from abstract_domains.state import State
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

    def get_node_result(self, node: Node) -> List[State]:
        """Get the analysis result for a node.
        
        :param node: analyzed node
        :return: list of states representing the result of the analysis for the block
        """
        return self.result[node]

    def set_node_result(self, node: Node, states: List[State]) -> None:
        """Set the analysis result for a node.
        
        :param node: analyzed node
        :param states: list of states representing the result of the analysis for the block
        """
        self.result[node] = states

    def __str__(self):
        """Analysis result string representation.
        
        :return: string representing the result of the analysis
        """
        result = []
        for identifier in self.cfg.nodes:
            node = self.cfg.nodes[identifier]
            result.append("********* {} *********".format(node))
            states = self.get_node_result(self.cfg.nodes[identifier])
            node = [item for items in zip_longest(states, node.stmts) for item in items if item is not None]
            result.append("\n".join("{}".format(item) for item in node))
        return "\n".join(res for res in result)
