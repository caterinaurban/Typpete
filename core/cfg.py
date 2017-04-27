from abc import ABC, abstractmethod
from core.statements import Statement
from enum import Enum
from typing import Dict, List, Set, Tuple, Generator


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
        IF_OUT = -2  # if exit edge
        LOOP_OUT = -1  # loop exit edge
        Default = 0
        LOOP_IN = 1  # loop entry edge
        IF_IN = 2  # if entry edge

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
    def __init__(self, source: Node, condition: Statement, target: Node, kind=Edge.Kind.Default):
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
        return "{0.source} -- {0.condition} -- {0.target}".format(self)


class ControlFlowGraph:
    def __init__(self, nodes: Set[Node], in_node: Node, out_node: Node, edges: Set[Edge] = set(), loose_in_edges=None,
                 loose_out_edges=None):
        """Control flow graph representation.
        
        :param nodes: set of nodes of the control flow graph
        :param in_node: entry node of the control flow graph
        :param out_node: exit node of the control flow graph
        :param edges: optional set of edges of the control flow graph
        :param loose_in_edges: optional set of loose edges that have no start yet and end inside this CFG
        :param loose_out_edges: optional set of loose edges that start inside this CFG and have no end yet
        """
        assert in_node or loose_in_edges
        assert out_node or loose_out_edges
        self._nodes = {node.identifier: node for node in nodes}
        self._in_node = in_node
        self._out_node = out_node
        self._edges = {(edge.source, edge.target): edge for edge in edges}
        self._loose_in_edges = loose_in_edges or set()
        self._loose_out_edges = loose_out_edges or set()

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

    @property
    def loose_in_edges(self):
        return self._loose_in_edges

    @property
    def loose_out_edges(self):
        return self._loose_out_edges

    @property
    def loose(self):
        return len(self.loose_in_edges) or len(self.loose_out_edges)

    def nodes_forward(self) -> Generator[Node, None, None]:
        worklist = [self.in_node]
        done = set()
        while worklist:
            current = worklist.pop()
            if current not in done:
                done.add(current)
                yield current
                for successor in self.successors(current):
                    worklist.insert(0, successor)

    def nodes_backward(self) -> Generator[Node, None, None]:
        worklist = [self.out_node]
        done = set()
        while worklist:
            current = worklist.pop()
            if current not in done:
                done.add(current)
                yield current
                for predecessor in self.predecessors(current):
                    worklist.insert(0, predecessor)

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

    def combine(self, other):
        self.nodes.update(other.nodes)
        self.edges.update(other.edges)
        self.loose_in_edges.update(other.loose_in_edges)
        self.loose_out_edges.update(other.loose_out_edges)
        return self

    def prepend(self, other):
        other.append(self)
        self.replace(other)

    def append(self, other):
        assert not (self.loose_out_edges and other.loose_in_edges)
        self.nodes.update(other.nodes)
        self.edges.update(other.edges)
        if self.loose_out_edges:
            for e in self.loose_out_edges:
                e._target = other.in_node
                self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add
            # clear loose edge sets
            self._loose_out_edges = set()
        elif other.loose_in_edges:
            for e in other.loose_in_edges:
                e._source = self.out_node
                self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add
            # clear loose edge sets
            other._loose_in_edges = set()
        else:
            # neither of the CFGs has loose ends -> add unconditional edge
            e = Unconditional(self.out_node, other.in_node)
            self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add

        # in any case, transfer loose_out_edges of other to self
        self._loose_out_edges = other.loose_out_edges
        self._out_node = other.out_node

        return self

    def replace(self, other):
        self.__dict__.update(other.__dict__)
