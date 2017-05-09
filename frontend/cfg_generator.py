import optparse
import sys
import typing

from visualization.graph_renderer import CfgRenderer
import ast
from core.cfg import *
from core.statements import *
from core.expressions import *


def main(args):
    optparser = optparse.OptionParser(usage="python3.6 -m frontend.cfg_generator [options] [string]")
    optparser.add_option("-f", "--file",
                         help="Read a code snippet from the specified file")
    optparser.add_option("-l", "--label",
                         help="The label for the visualization")

    options, args = optparser.parse_args(args)
    if options.file:
        with open(options.file) as instream:
            code = instream.read()
        label = options.file
    elif len(args) == 2:
        code = args[1] + "\n"
        label = "<code read from command line parameter>"
    else:
        print("Expecting Python code on stdin...")
        code = sys.stdin.read()
        label = "<code read from stdin>"
    if options.label:
        label = options.label

    cfg = source_to_cfg(code)

    CfgRenderer().render(cfg, label=label)


class LooseControlFlowGraph:
    def __init__(self, nodes: Set[Node] = None, in_node: Node = None, out_node: Node = None, edges: Set[Edge] = None,
                 loose_in_edges=None,
                 loose_out_edges=None, both_loose_edges=None):
        """Loose control flow graph representation.

        This representation uses a complete (non-loose) control flow graph via aggregation and adds loose edges and
        some transformations methods to combine, prepend and append loose control flow graphs. This class
        intentionally does not provide access to the linked CFG. The completed CFG can be retrieved finally with
        `eject()`.

        :param nodes: optional set of nodes of the control flow graph
        :param in_node: optional entry node of the control flow graph
        :param out_node: optional exit node of the control flow graph
        :param edges: optional set of edges of the control flow graph
        :param loose_in_edges: optional set of loose edges that have no start yet and end inside this CFG
        :param loose_out_edges: optional set of loose edges that start inside this CFG and have no end yet
        :param both_loose_edges: optional set of loose edges, loose on both ends
        """
        assert not in_node or not (loose_in_edges or both_loose_edges)
        assert not out_node or not (loose_out_edges or both_loose_edges)
        assert all([e.source is None for e in loose_in_edges or []])
        assert all([e.target is None for e in loose_out_edges or []])
        assert all([e.source is None and e.target is None for e in both_loose_edges or []])

        self._cfg = ControlFlowGraph(nodes or set(), in_node, out_node, edges or set())
        self._loose_in_edges = loose_in_edges or set()
        self._loose_out_edges = loose_out_edges or set()
        self._both_loose_edges = both_loose_edges or set()

    @property
    def nodes(self) -> Dict[int, Node]:
        return self._cfg.nodes

    @property
    def in_node(self) -> Node:
        return self._cfg.in_node

    @property
    def out_node(self) -> Node:
        return self._cfg.out_node

    @property
    def edges(self) -> Dict[Tuple[Node, Node], Edge]:
        return self._cfg.edges

    @property
    def loose_in_edges(self):
        return self._loose_in_edges

    @property
    def loose_out_edges(self):
        return self._loose_out_edges

    @property
    def both_loose_edges(self):
        return self._both_loose_edges

    def loose(self):
        return len(self.loose_in_edges) or len(self.loose_out_edges) or len(self.both_loose_edges)

    def combine(self, other):
        assert not (self.in_node and other.in_node)
        assert not (self.out_node and other.out_node)
        self.nodes.update(other.nodes)
        self.edges.update(other.edges)
        self.loose_in_edges.update(other.loose_in_edges)
        self.loose_out_edges.update(other.loose_out_edges)
        self.both_loose_edges.update(other.both_loose_edges)
        self._cfg._in_node = other.in_node or self.in_node  # agree on in_node
        self._cfg._out_node = other.out_node or self.out_node  # agree on out_node
        return self

    def prepend(self, other):
        other.append(self)
        self.replace(other)

    def append(self, other):
        assert not (self.loose_out_edges and other.loose_in_edges)
        assert not self.both_loose_edges or (not other.loose_in_edges and not other.both_loose_edges)

        self.nodes.update(other.nodes)
        self.edges.update(other.edges)

        edge_added = False
        if self.loose_out_edges:
            edge_added = True
            for e in self.loose_out_edges:
                e._target = other.in_node
                self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add
            # clear loose edge sets
            self._loose_out_edges = set()
        elif other.loose_in_edges:
            edge_added = True
            for e in other.loose_in_edges:
                e._source = self.out_node
                self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add
            # clear loose edge set
            other._loose_in_edges = set()

        if self.both_loose_edges:
            edge_added = True
            for e in self.both_loose_edges:
                e._target = other.in_node
                self.loose_in_edges.add(e)  # updated/created edge is not yet in edge dict -> add
            # clear loose edge set
            self._both_loose_edges = set()
        elif other.both_loose_edges:
            edge_added = True
            for e in other.both_loose_edges:
                e._source = self.in_node
                self.loose_out_edges.add(e)  # updated/created edge is not yet in edge dict -> add
                # clearing loose edge set is not necessary since other is no longer used
        if not edge_added:
            # neither of the CFGs has loose ends -> add unconditional edge
            e = Unconditional(self.out_node, other.in_node)
            self.edges[(e.source, e.target)] = e  # updated/created edge is not yet in edge dict -> add

        # in any case, transfer loose_out_edges of other to self
        self._loose_out_edges |= other.loose_out_edges
        self._cfg._out_node = other.out_node

        return self

    def eject(self) -> ControlFlowGraph:
        if self.loose():
            raise TypeError('This control flow graph is still loose and can not eject a complete control flow graph!')
        return self._cfg

    def replace(self, other):
        self.__dict__.update(other.__dict__)


class NodeIdentifierGenerator:
    """
    A helper class to generate a increasing sequence of node identifiers.
    """

    def __init__(self):
        """
        Creates a sequencer which will return 1 as the first id.
        """
        self._next = 0

    @property
    def next(self):
        self._next += 1
        return self._next


class CfgFactory:
    """
    A helper class that encapsulates a partial CFG and possibly some statements not yet attached to CFG.

    Whenever the
    method `complete_basic_block()` is called, it is ensured that all unattached statements are properly attached to
    partial CFG. The partial CFG can be retrieved at any time by property `cfg`.
    """

    def __init__(self, id_gen):
        self._stmts = []
        self._cfg = None
        self._id_gen = id_gen

    @property
    def cfg(self):
        return self._cfg

    def prepend_cfg(self, other):
        if self._cfg is not None:
            self._cfg.prepend(other)
        else:
            self._cfg = other
        return self._cfg

    def append_cfg(self, other):
        if self._cfg is not None:
            self._cfg.append(other)
        else:
            self._cfg = other
        return self._cfg

    def add_stmts(self, stmts):
        """
        Adds statements to the currently open block.
        :param stmts: a single statement or an iterable of statements
        :return:
        """
        if isinstance(stmts, (List, Tuple)):
            self._stmts += list(stmts)
        else:
            self._stmts.append(stmts)

    def complete_basic_block(self):
        if self._stmts:
            block = Basic(self._id_gen.next, self._stmts)
            self.append_cfg(LooseControlFlowGraph({block}, block, block, set()))
            self._stmts = []


# noinspection PyMethodMayBeStatic,PyPep8Naming
class CfgVisitor(ast.NodeVisitor):
    """
    This AST visitor generates a CFG recursively.

    Overwritten methods return either a partial CFG or a statement/expression, depending on the type of node.
    """

    def __init__(self):
        super().__init__()
        self._id_gen = NodeIdentifierGenerator()

    def visit_Num(self, node):
        l = Literal(int, node.n)
        return l

    def visit_Str(self, node):
        l = Literal(str, node.s)
        return l

    def visit_Name(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        v = self._ensure_stmt(pp, VariableIdentifier(int, node.id))
        return v

    def visit_Assign(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        value = self._ensure_stmt_visit(node.value)
        stmts = [Assignment(pp, self._ensure_stmt_visit(target), value) for
                 target in node.targets]
        return stmts

    def visit_Module(self, node):
        start_cfg = self._dummy_cfg()
        body_cfg = self._translate_body(node.body, allow_loose_in_edges=True, allow_loose_out_edges=True)
        end_cfg = self._dummy_cfg()

        return start_cfg.append(body_cfg).append(end_cfg)

    def visit_If(self, node):
        body_cfg = self._translate_body(node.body)

        pp_test = ProgramPoint(node.test.lineno, node.test.col_offset)
        test = self.visit(node.test)
        neg_test = Call(pp_test, "not", [test], bool)

        body_cfg.loose_in_edges.add(Conditional(None, test, body_cfg.in_node, Edge.Kind.IF_IN))
        body_cfg.loose_out_edges.add(Unconditional(body_cfg.out_node, None, Edge.Kind.IF_OUT))
        if node.orelse:  # if there is else branch
            orelse_cfg = self._translate_body(node.orelse)
            orelse_cfg.loose_in_edges.add(Conditional(None, neg_test, orelse_cfg.in_node, Edge.Kind.IF_IN))
            orelse_cfg.loose_out_edges.add(Unconditional(orelse_cfg.out_node, None, Edge.Kind.IF_OUT))
        else:
            orelse_cfg = LooseControlFlowGraph()
            orelse_cfg.both_loose_edges.add(Conditional(None, neg_test, None, Edge.Kind.DEFAULT))

        cfg = body_cfg.combine(orelse_cfg)
        return cfg

    def visit_While(self, node):
        dummy_header_cfg = self._dummy_cfg()

        body_cfg = self._translate_body(node.body)

        pp_test = ProgramPoint(node.test.lineno, node.test.col_offset)
        test = self.visit(node.test)
        neg_test = Call(pp_test, "not", [test], bool)

        body_cfg.loose_in_edges.add(Conditional(None, test, body_cfg.in_node, Edge.Kind.LOOP_IN))
        test_fail_cfg = LooseControlFlowGraph()
        test_fail_cfg.both_loose_edges.add(Conditional(None, neg_test, None, Edge.Kind.DEFAULT))

        dummy_header_in_node = dummy_header_cfg.in_node
        body_cfg_out_node = body_cfg.out_node

        cfg = body_cfg.combine(test_fail_cfg)
        cfg.prepend(dummy_header_cfg)

        back_edge = Unconditional(body_cfg_out_node, dummy_header_in_node, Edge.Kind.LOOP_OUT)
        cfg.edges[(back_edge.source, back_edge.target)] = back_edge

        if node.orelse:  # if there is else branch
            orelse_cfg = self._translate_body(node.orelse)
            cfg.append(orelse_cfg)

        return cfg

    def visit_UnaryOp(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        operand = self.visit(node.operand)
        return Call(pp, type(node.op).__name__.lower(), [operand], int)

    def visit_BinOp(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        return Call(pp, type(node.op).__name__.lower(),
                    [self._ensure_stmt_visit(node.left), self._ensure_stmt_visit(node.right)], int)

    def visit_BoolOp(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        return Call(pp, type(node.op).__name__.lower(),
                    [self._ensure_stmt_visit(val) for val in node.values], bool)

    def visit_Compare(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        last_comp = self._ensure_stmt_visit(node.comparators[0])
        result = Call(pp, type(node.ops[0]).__name__.lower(),
                      [self._ensure_stmt_visit(node.left),
                       last_comp],
                      bool)
        for op, comp in list(zip(node.ops, node.comparators))[1:]:
            cur_call = Call(pp, type(op).__name__.lower(),
                            [last_comp,
                             self._ensure_stmt_visit(comp)],
                            bool)
            result = Call(pp, 'and',
                          [result,
                           cur_call],
                          bool)
        return result

    def visit_NameConstant(self, node):
        return Literal(bool, node.value)

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Call(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        return Call(pp, node.func.id, [self.visit(arg) for arg in node.args], typing.Any)

    def generic_visit(self, node):
        print(type(node).__name__)
        super().generic_visit(node)

    def _dummy(self):
        return Basic(self._id_gen.next, list())

    def _dummy_cfg(self):
        dummy = self._dummy()
        return LooseControlFlowGraph({dummy}, dummy, dummy, set())

    def _translate_body(self, body, allow_loose_in_edges=False, allow_loose_out_edges=False):
        cfg_factory = CfgFactory(self._id_gen)

        for child in body:
            if isinstance(child, (ast.Assign, ast.Expr)):
                cfg_factory.add_stmts(self.visit(child))
            elif isinstance(child, ast.If):
                cfg_factory.complete_basic_block()
                if_cfg = self.visit(child)
                cfg_factory.append_cfg(if_cfg)
            elif isinstance(child, ast.While):
                cfg_factory.complete_basic_block()
                while_cfg = self.visit(child)
                cfg_factory.append_cfg(while_cfg)
            elif isinstance(child, ast.Pass):
                pass
            else:
                raise NotImplementedError(f"The statement {str(type(child))} is not yet translatable to CFG!")
        cfg_factory.complete_basic_block()

        if not allow_loose_in_edges and cfg_factory.cfg and cfg_factory.cfg.loose_in_edges:
            cfg_factory.prepend_cfg(self._dummy_cfg())
        if not allow_loose_out_edges and cfg_factory.cfg and cfg_factory.cfg.loose_out_edges:
            cfg_factory.append_cfg(self._dummy_cfg())

        return cfg_factory.cfg

    @staticmethod
    def _ensure_stmt(pp, expr):
        if isinstance(expr, Statement):
            return expr
        elif isinstance(expr, Literal):
            return LiteralEvaluation(pp, expr)
        elif isinstance(expr, VariableIdentifier):
            return VariableAccess(pp, expr)
        else:
            raise NotImplementedError(f"The expression {str(type(expr))} is not yet translatable to CFG!")

    def _ensure_stmt_visit(self, node):
        result = self.visit(node)
        pp = ProgramPoint(node.lineno, node.col_offset)
        return CfgVisitor._ensure_stmt(pp, result)


def ast_to_cfg(root_node):
    """
    Create the control flow graph from a ast node.
    :param root_node: the root node of the AST to be translated to CFG
    :return: the CFG of the passed AST.
    """
    loose_cfg = CfgVisitor().visit(root_node)
    return loose_cfg.eject()


def source_to_cfg(code):
    """
    Parses the given code and creates its control flow graph.
    :param code: the code as a string
    :return: the CFG of code
    """
    root_node = ast.parse(code)
    return ast_to_cfg(root_node)


if __name__ == '__main__':
    main(sys.argv)
