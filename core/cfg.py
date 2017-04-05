from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List
from statements import Statement

class Node(metaclass=ABCMeta):

    def __init__(self, id: int, stmts: List[Statement]):
        """Node of a control flow graph.

        :param id: the identifier associated with the node
        :param stmts: the list of statements stored in the node 
        """
        self.id = id
        self.stmts = stmts

    @abstractmethod
    def __str__(self):
        pass


class BasicBlock(Node):

    def __init__(self, id: int, stmts: List[Statement]):
        """Basic block of a control flow graph.
        
        :param id: the identifier associated with the block  
        :param stmts: the list of statements stored in the block 
        """
        super().__init__(id, stmts)

    def __str__(self):
        return str(self.id)


class Edge(metaclass=ABCMeta):

    class Kind(Enum):
        """Kind of an edge of a control flow graph."""
        Out = -1        # loop exit edge
        Default = 0
        In = 1          # loop entry edge

    def __init__(self, source: Node, target: Node, kind=Kind.Default):
        """Edge of a control flow graph.
        
        :param source: the source node of the edge
        :param target: the target node of the edge
        :param kind: the kind of the edge
        """
        self.source = source
        self.target = target
        self.kind = kind

    def is_in(self):
        return self.kind is Edge.Kind.In

    def is_out(self):
        return self.kind is Edge.Kind.Out


class UnconditionalEdge(Edge):

    def __init__(self, source: Node, target: Node, kind=Edge.Kind.Default):
        """Unconditional edge of a control flow graph.

        :param source: the source node of the edge
        :param target: the target node of the edge
        :param kind: the kind of the edge
        """
        super().__init__(source, target, kind)


class ConditionalEdge(Edge):

    def __init__(self, source: Node, target: Node, condition: Statement, kind=Edge.Kind.Default):
        """Conditional edge of a control flow graph.
        
        :param source: the source node of the edge
        :param target: the target node of the edge
        :param condition: the condition associated with the edge
        :param kind: the kind of the edge
        """
        super().__init__(source, target, kind)
        self.condition = condition


class ControlFlowGraph(metaclass=ABCMeta):

    def __init__(self, nodes: List[Node], entry: Node, exit: Node, edges: List[Edge]):
        """Control flow graph representation.
        
        :param nodes: the nodes of the control flow graph
        :param entry: the entry node of the control flow graph
        :param exit: the exit node of the control flow graph
        :param edges: the edges of the control flow graph
        """
        self.nodes = nodes
        self.entry = entry
        self.exit = exit
        self.edges = edges
