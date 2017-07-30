from core.cfg import *
import graphviz as gv
from itertools import zip_longest
import numbers
from uuid import uuid4 as uuid
import html


class GraphRenderer(metaclass=ABCMeta):
    """Graphviz rendering."""

    graph_attr = {
        'labelloc': 't',
        'fontcolor': 'black',
        'fontname': 'roboto',
        'bgcolor': '#ffffff',
        'margin': '0',
    }   # graph attributes

    node_attr = {
        'color': 'black',
        'fontcolor': 'black',
        'fontname': 'roboto',
        'style': 'filled',
        'fillcolor': '#70a6ff',
        'forcelabels': 'true'
    }   # node attributes

    edge_attr = {
        'color': '#565656',
        'fontcolor': '#565656',
        'fontname': 'roboto',
        'fontsize': '12'
    }   # edge attributes

    _graph = None           # graph to be rendered
    _rendered = None        # rendered nodes
    _max_label_len = 100    # maximum length for labels

    @staticmethod
    def _escape_label(label):
        """Escape special characters in DOT label."""
        return label.replace("\\", "\\\\").replace("|", "\\|").replace("<", "\\<").replace(">", "\\>")

    def _shorten_label(self, label):
        """Shorten long labels."""
        if len(label) > self._max_label_len - 3:
            half = int((self._max_label_len - 3) / 2)
            return label[:half] + "..." + label[-half:]
        return label

    @staticmethod
    def _list2table(lst, escape=True):
        """Turn a list into an HTML table (to be used as a DOT label)."""
        table = '<<table border="0" cellborder="0">{}</table>>'     # table HTML format
        row = '<tr><td align="center">{}</td></tr>'                 # row HTML format
        escape_function = html.escape if escape else lambda x: x
        return table.format("\n".join(map(row.format, map(lambda x: escape_function(str(x)), lst or [""]))))

    @abstractmethod
    def _render(self, data):
        """Graphviz rendering of data.

        :param data: the data to be rendered
        """

    def render(self, data, label=None, filename="Graph", directory="graphs", view=True):
        """Graphviz rendering."""

        # create the Graphviz graph
        graph_attr = self.graph_attr.copy()
        if label is not None:
            graph_attr['label'] = self._escape_label(label)
        graph = gv.Digraph(graph_attr=graph_attr, node_attr=self.node_attr, edge_attr=self.edge_attr)

        # draw nodes and edges of the Graphviz graph
        self._graph = graph
        self._rendered = set()
        self._render(data)
        self._graph = None
        self._rendered = None

        # display the Graphviz graph
        graph.format = "pdf"
        graph.render(f"{filename}.gv", directory, view, cleanup=True)


class ListDictTreeRenderer(GraphRenderer):
    """Graphviz rendering of dictionaries and lists."""

    def _render(self, data):
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

        if node_id not in self._rendered:
            self._rendered.add(node_id)
            if isinstance(node, dict):
                self._render_dict(node, node_id)
            elif isinstance(node, list):
                self._render_list(node, node_id)
            else:
                self._graph.node(node_id, label=self._escape_label(self._shorten_label(repr(node))))

        return node_id

    def _render_dict(self, node, node_id):
        self._graph.node(node_id, label=node.get("node_type", "[dict]"))
        for key, value in node.items():
            if key == "node_type":
                continue
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_label(key))

    def _render_list(self, node, node_id):
        self._graph.node(node_id, label="[list]")
        for idx, value in enumerate(node):
            child_node_id = self._render_node(value)
            self._graph.edge(node_id, child_node_id, label=self._escape_label(str(idx)))


class CfgRenderer(GraphRenderer):
    """Graphviz rendering of a control flow graph."""

    def _node_color(self, node, cfg):
        fillcolor = self.node_attr['fillcolor']
        if node is cfg.in_node:
            fillcolor = '#24bf26'
        elif node is cfg.out_node:
            fillcolor = '#ce3538'
        elif any(edge.kind == Edge.Kind.LOOP_IN for edge in cfg.out_edges(node)):
            fillcolor = '#f4b942'
        return fillcolor

    def _render_node(self, node, label, fillcolor):
        if isinstance(node, (Basic, Loop)):
            self._graph.node(str(node), label=label, xlabel=str(node.identifier), fillcolor=fillcolor, shape='box')
        else:
            self._graph.node(str(node), label=label, xlabel=str(node.identifier), fillcolor=fillcolor, shape='circle')

    def _render_edge(self, edge):
        kind = edge.kind.name if edge.kind != Edge.Kind.DEFAULT else ""
        source = str(edge.source.identifier)
        target = str(edge.target.identifier)
        if isinstance(edge, Conditional):
            label = self._escape_label((kind + ": " if kind else "") + str(edge.condition))
            self._graph.edge(source, target, label=label)
        elif isinstance(edge, Unconditional):
            self._graph.edge(source, target, label=self._escape_label(kind))
        else:
            self._graph.edge(source, target, label=self._escape_label(str(edge)))

    def _render_edges(self, cfg):
        for edge in cfg.edges.values():
            self._render_edge(edge)

    def _render(self, cfg):
        for node in cfg.nodes.values():
            fillcolor = self._node_color(node, cfg)
            if isinstance(node, (Basic, Loop)):
                stmt = '<font color="#ffffff" point-size="11">{} </font>'
                stmts = map(lambda x: stmt.format(html.escape(str(x))), node.stmts)
                label = self._list2table(list(stmts), escape=False)
            else:
                label = self._escape_label(self._shorten_label(str(node)))
            self._render_node(node, label, fillcolor)
        self._render_edges(cfg)


class AnalysisResultRenderer(CfgRenderer):
    """Graphviz rendering of an analysis result on the analyzed control flow graph."""

    def _basic_node_label(self, node, result):
        state = '<font point-size="9">{} </font>'
        states = map(lambda x: state.format(html.escape(str(x)).replace('\n', '<br />')), result.get_node_result(node))
        stmt = '<font color="#ffffff" point-size="11">{}</font>'
        stmts = map(lambda x: stmt.format(html.escape(str(x))), node.stmts)
        node_result = [item for items in zip_longest(states, stmts) for item in items if item is not None]
        return self._list2table(node_result, escape=False)

    def _render(self, data):
        (cfg, result) = data
        for node in cfg.nodes.values():
            fillcolor = self._node_color(node, cfg)
            if isinstance(node, (Basic, Loop)):
                label = self._basic_node_label(node, result)
                self._render_node(node, label, fillcolor)
            else:
                label = self._escape_label(self._shorten_label(str(node)))
                self._render_node(node, label, fillcolor)
        self._render_edges(cfg)
