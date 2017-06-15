from core.cfg import *
import graphviz as gv
from itertools import zip_longest
import numbers
from uuid import uuid4 as uuid
import html


class GraphRenderer:
    graphattrs = {
        'labelloc': 't',
        'fontcolor': 'black',
        'fontname': 'roboto',
        'bgcolor': '#FFFFFF',
        'margin': '0',
    }

    nodeattrs = {
        'color': 'black',
        'fontcolor': 'black',
        'fontname': 'roboto',
        'style': 'filled',
        'fillcolor': '#70a6ff',
        'forcelabels': 'true'
    }

    edgeattrs = {
        'color': '#565656',
        'fontcolor': '#565656',
        'fontname': 'roboto',
    }

    _graph = None
    _rendered_nodes = None
    _max_label_len = 100

    @staticmethod
    def _escape_dot_label(label):
        return label.replace("\\", "\\\\").replace("|", "\\|").replace("<", "\\<").replace(">", "\\>")

    def _shorten_string(self, string):
        if len(string) > self._max_label_len - 3:
            halflen = int((self._max_label_len - 3) / 2)
            return string[:halflen] + "..." + string[-halflen:]
        return string

    @staticmethod
    def _list2lines(l, escape=True):
        escape_func = html.escape if escape else lambda x: x
        return '''<<TABLE BORDER="0" CELLBORDER="0">{}</TABLE>>'''.format(
            '\n'.join(map('''<TR><TD ALIGN="LEFT">{}</TD></TR>'''.format,
                          map(lambda s: escape_func(str(s)), l or [""]))))

    @abstractmethod
    def _render_graph(self, data):
        """
        Entry point for rendering graph represented by data.
        :param data: the whole data necessary to render graph
        :return:
        """

    def render(self, data, label=None, filename="Graph", directory="graphs", view=True):
        # create the graph
        graphattrs = self.graphattrs.copy()
        if label is not None:
            graphattrs['label'] = self._escape_dot_label(label)
        graph = gv.Digraph(graph_attr=graphattrs, node_attr=self.nodeattrs, edge_attr=self.edgeattrs)

        # recursively draw all the nodes and edges
        self._graph = graph
        self._rendered_nodes = set()
        self._render_graph(data)
        self._graph = None
        self._rendered_nodes = None

        # display the graph
        graph.format = "pdf"
        graph.render(f"{filename}.gv", directory, view, cleanup=True)


class ListDictTreeRenderer(GraphRenderer):
    """
    this class is capable of rendering data structures consisting of
    dicts and lists as a graph using graphviz
    """

    def _render_graph(self, data):
        self._render_node(data)

    def _render_node(self, node):
        """
        Renders a node. Recursive callee for node rendering.
        :param node: the representation of a node (dependent of rendered data structure)
        :return: node id of created node
        """
        if isinstance(node, (str, numbers.Number)) or node is None:
            node_id = uuid()
        else:
            node_id = id(node)
        node_id = str(node_id)

        if node_id not in self._rendered_nodes:
            self._rendered_nodes.add(node_id)
            if isinstance(node, dict):
                self._render_dict(node, node_id)
            elif isinstance(node, list):
                self._render_list(node, node_id)
            else:
                self._graph.node(node_id, label=self._escape_dot_label(self._shorten_string(repr(node))))

        return node_id

    def _render_dict(self, node, node_id):
        self._graph.node(node_id, label=node.get("node_type", "[dict]"))
        for key, value in node.items():
            if key == "node_type":
                continue
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_dot_label(key))

    def _render_list(self, node, node_id):
        self._graph.node(node_id, label="[list]")
        for idx, value in enumerate(node):
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_dot_label(str(idx)))


class CfgRenderer(GraphRenderer):
    """
    this class is capable of rendering a cfg
    """

    def _render_graph(self, cfg):
        for node_id, node in cfg.nodes.items():
            fillcolor = self.nodeattrs['fillcolor']
            if node is cfg.in_node:
                fillcolor = '#24bf26'
            elif node is cfg.out_node:
                fillcolor = '#ce3538'

            if isinstance(node, (Basic, Loop)):
                self._graph.node(str(node), label=self._list2lines(node.stmts),
                                 xlabel=str(node.identifier),
                                 fillcolor=fillcolor, shape='box')
            else:
                self._graph.node(str(node), label=self._escape_dot_label(self._shorten_string(str(node))),
                                 xlabel=str(node.identifier),
                                 fillcolor=fillcolor, shape='circle')

        for edge in cfg.edges.values():
            edge_kind = edge.kind.name if edge.kind != Edge.Kind.DEFAULT else ""
            if isinstance(edge, Conditional):
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(
                                     (edge_kind + ": " if edge_kind else '') + str(edge.condition)))
            elif isinstance(edge, Unconditional):
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(edge_kind))
            else:
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(str(edge)))


class AnalysisResultRenderer(GraphRenderer):
    """Rendering of an analysis result together with the analyzed control flow graph."""

    def _render_graph(self, data):
        (cfg, result) = data
        for node_id, node in cfg.nodes.items():
            fillcolor = self.nodeattrs['fillcolor']
            if node is cfg.in_node:
                fillcolor = '#24bf26'
            elif node is cfg.out_node:
                fillcolor = '#ce3538'

            if isinstance(node, (Basic, Loop)):
                states = result.get_node_result(node)
                # special format states here and pass formatted strings along
                states = map(lambda x: '<FONT COLOR="#191919" POINT-SIZE="11">{}</FONT>'.format(html.escape(str(x))), states)
                stmts = map(lambda x: '<B>{}</B>'.format(html.escape(str(x))), node.stmts)
                node_result = [item for items in zip_longest(states, stmts) for item in items if item is not None]
                self._graph.node(str(node), label=self._list2lines(node_result, escape=False),
                                 xlabel=str(node.identifier),
                                 fillcolor=fillcolor, shape='box')
            else:
                self._graph.node(str(node), label=self._escape_dot_label(self._shorten_string(str(node))),
                                 xlabel=str(node.identifier),
                                 fillcolor=fillcolor, shape='circle')

        for edge in cfg.edges.values():
            edge_kind = edge.kind.name if edge.kind != Edge.Kind.DEFAULT else ""
            if isinstance(edge, Conditional):
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(
                                     (edge_kind + ": " if edge_kind else '') + str(edge.condition)))
            elif isinstance(edge, Unconditional):
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(edge_kind))
            else:
                self._graph.edge(str(edge.source.identifier), str(edge.target.identifier),
                                 label=self._escape_dot_label(str(edge)))