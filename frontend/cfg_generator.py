import re
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

    cfg = generate_cfg(code)

    CfgRenderer().render(cfg, label=label)


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

    def add_stmt(self, stmt):
        self._stmts.append(stmt)

    def complete_basic_block(self):
        if self._stmts:
            block = Basic(self._id_gen.next, self._stmts)
            self.append_cfg(ControlFlowGraph({block}, block, block))
            self._stmts = []


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

    def visit_Name(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        v = self._ensure_stmt(pp, VariableIdentifier(int, node.id))
        return v

    def visit_Assign(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        pp_target = ProgramPoint(node.targets[0].lineno, node.targets[0].col_offset)
        pp_value = ProgramPoint(node.value.lineno, node.value.col_offset)
        target = self.visit(node.targets[0])  # TODO add multiple lefts support
        value = self.visit(node.value)  # TODO add multiple lefts support
        stmt = Assignment(pp, CfgVisitor._ensure_stmt(pp_target, target), CfgVisitor._ensure_stmt(pp_value, value))
        return stmt

    def visit_Module(self, node):
        start_cfg = self._dummy_cfg()
        body_cfg = self._translate_body(node.body, allow_loose_in_edges=True, allow_loose_out_edges=True)
        end_cfg = self._dummy_cfg()

        return start_cfg.append(body_cfg).append(end_cfg)

    def visit_If(self, node):
        body_cfg = self._translate_body(node.body)
        orelse_cfg = self._translate_body(node.orelse)

        pp_test = ProgramPoint(node.test.lineno, node.test.col_offset)
        test = self.visit(node.test)
        neg_test = Call(pp_test, "not", [test], bool)

        body_cfg.loose_in_edges.add(Conditional(None, test, body_cfg.in_node, Edge.Kind.IF_IN))
        body_cfg.loose_out_edges.add(Unconditional(body_cfg.out_node, None, Edge.Kind.IF_OUT))
        if orelse_cfg:  # if there is a else branch
            orelse_cfg.loose_in_edges.add(Conditional(None, neg_test, orelse_cfg.in_node, Edge.Kind.IF_IN))
            orelse_cfg.loose_out_edges.add(Unconditional(orelse_cfg.out_node, None, Edge.Kind.IF_OUT))

            cfg = body_cfg.combine(orelse_cfg)
        else:
            cfg = body_cfg
        return cfg

    def visit_UnaryOp(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        operand = self.visit(node.operand)
        return Call(pp, type(node.op).__name__.lower(), [operand], int)

    def visit_BinOp(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        left = self.visit(node.left)
        right = self.visit(node.right)
        return Call(pp, type(node.op).__name__.lower(), [left, right], int)

    def visit_Compare(self, node):
        pp = ProgramPoint(node.lineno, node.col_offset)
        left = self.visit(node.left)
        op = node.ops[0]  # TODO add multiple operators support
        right = self.visit(node.comparators[0])  # TODO add multiple comparators support
        return Call(pp, type(op).__name__.lower(), [left, right], bool)

    def visit_NameConstant(self, node):
        return Literal(bool, node.value)

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Call(self, node):
        return Call(bool, node.func.id, [self.visit(arg) for arg in node.args], typing.Any)

    def generic_visit(self, node):
        print(type(node).__name__)
        super().generic_visit(node)

    def _dummy(self):
        return Basic(self._id_gen.next, list())

    def _dummy_cfg(self):
        dummy = self._dummy()
        return ControlFlowGraph({dummy}, dummy, dummy)

    def _translate_body(self, body, allow_loose_in_edges=False, allow_loose_out_edges=False):
        cfg_factory = CfgFactory(self._id_gen)

        for child in body:
            if isinstance(child, (ast.Assign, ast.Expr)):
                cfg_factory.add_stmt(self.visit(child))
            elif isinstance(child, ast.If):
                cfg_factory.complete_basic_block()
                if_cfg = self.visit(child)
                cfg_factory.append_cfg(if_cfg)
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


def generate_cfg(code):
    """
    Parses the given code and creates its control-flow-graph.
    :param code: the code as a string
    :return: the CFG of code
    """

    root_node = ast.parse(code)
    cfg = CfgVisitor().visit(root_node)

    return cfg


if __name__ == '__main__':
    main(sys.argv)
