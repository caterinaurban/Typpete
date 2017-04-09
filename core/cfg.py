from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Set, Tuple
from statements import Statement


class Node(ABC):
    def __init__(self, identifier: int, stmts: List[Statement]):
        """Node of a control flow graph.

        :param identifier: identifier associated with the node
        :param stmts: list of statements stored in the node 
        """
        self._identifier = identifier
        self._stmts = stmts

    @property
    def identifier(self):
        return self._identifier

    @property
    def stmts(self):
        return self._stmts

    def __eq__(self, other: 'Node'):
        return self.identifier == other.identifier

    def __hash__(self):
        return hash(self.identifier)

    def __ne__(self, other: 'Node'):
        return not (self == other)

    def __repr__(self):
        return str(self)

    @abstractmethod
    def __str__(self):
        """Node string representation.  
        
        :return: string representing the node
        """

    def size(self):
        """Number of statements stored in the node.
        
        :return: number of statements stored in the node 
        """
        return len(self.stmts)


class Basic(Node):
    def __init__(self, identifier: int, stmts: List[Statement]):
        """Basic node of a control flow graph.
        
        :param identifier: identifier associated with the node  
        :param stmts: list of statements stored in the node 
        """
        super().__init__(identifier, stmts)

    def __str__(self):
        return str(self.identifier)


class Loop(Node):
    def __init__(self, identifier: int, stmts: List[Statement] = list()):
        """Loop head node of a control flow graph.

        :param identifier: identifier associated with the block  
        :param stmts: list of statements stored in the block 
        """
        super().__init__(identifier, stmts)

    def __str__(self):
        return str(self.identifier)


class Edge(ABC):
    class Kind(Enum):
        """Kind of an edge of a control flow graph."""
        Out = -1  # loop exit edge
        Default = 0
        In = 1  # loop entry edge

    def __init__(self, source: Node, target: Node, kind: Kind = Kind.Default):
        """Edge of a control flow graph.
        
        :param source: source node of the edge
        :param target: target node of the edge
        :param kind: kind of the edge
        """
        self._source = source
        self._target = target
        self._kind = kind

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def kind(self):
        return self._kind

    def __eq__(self, other: 'Edge'):
        return (self.source, self.target) == (other.source, other.target)

    def __hash__(self):
        return hash((self.source, self.target))

    def __ne__(self, other: 'Edge'):
        return not (self == other)

    def __repr__(self):
        return str(self)

    @abstractmethod
    def __str__(self):
        """Edge string representation.  

        :return: string representing the edge
        """

    def is_in(self):
        return self.kind is Edge.Kind.In

    def is_out(self):
        return self.kind is Edge.Kind.Out


class Unconditional(Edge):
    def __init__(self, source: Node, target: Node, kind=Edge.Kind.Default):
        """Unconditional edge of a control flow graph.

        :param source: source node of the edge
        :param target: target node of the edge
        :param kind: kind of the edge
        """
        super().__init__(source, target, kind)

    def __str__(self):
        return "{0.source} -- {0.target}".format(self)


class Conditional(Edge):
    def __init__(self, source: Node, target: Node, condition: Statement, kind=Edge.Kind.Default):
        """Conditional edge of a control flow graph.
        
        :param source: source node of the edge
        :param target: target node of the edge
        :param condition: condition associated with the edge
        :param kind: kind of the edge
        """
        super().__init__(source, target, kind)
        self._condition = condition

    @property
    def condition(self):
        return self._condition

    def __str__(self):
        return "{0.source} -{0.condition}- {0.target}".format(self)


class ControlFlowGraph(object):
    def __init__(self, nodes: Set[Node], in_node: Node, out_node: Node, edges: Set[Edge]):
        """Control flow graph representation.
        
        :param nodes: nodes of the control flow graph
        :param in_node: entry node of the control flow graph
        :param out_node: exit node of the control flow graph
        :param edges: edges of the control flow graph
        """
        self._nodes = {node.identifier: node for node in nodes}
        self._in_node = in_node
        self._out_node = out_node
        self._edges = {(edge.source, edge.target): edge for edge in edges}

    @property
    def nodes(self) -> Dict[int, Node]:
        return self._nodes

    @property
    def in_node(self) -> Node:
        return self._in_node

    @property
    def out_node(self) -> Node:
        return self._out_node

    @property
    def edges(self) -> Dict[Tuple[Node, Node], Edge]:
        return self._edges

    def in_edges(self, node: Node) -> Set[Edge]:
        """Ingoing edges of a given node.
        
        :param node: given node
        :return: set of ingoing edges of the node
        """
        return {self.edges[(source, target)] for (source, target) in self.edges if target == node}

    def predecessors(self, node: Node) -> Set[Node]:
        """Predecessors of a given node.

        :param node: given node
        :return: set of predecessors of the node
        """
        return {edge.source for edge in self.in_edges(node)}

    def out_edges(self, node: Node) -> Set[Edge]:
        """Outgoing edges of a given node.

        :param node: given node
        :return: set of outgoing edges of the node
        """
        return {self.edges[(source, target)] for (source, target) in self.edges if source == node}

    def successors(self, node: Node) -> Set[Node]:
        """Successors of a given node.
        
        :param node: given node
        :return: set of successors of the node
        """
        return {edge.target for edge in self.out_edges(node)}
