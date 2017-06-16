from unittest import TestCase

from abstract_domains.dummies import ExpressionStore
from abstract_domains.numerical.interval import IntervalStore
from core.expressions import VariableIdentifier
from engine.forward import ForwardInterpreter
from frontend.cfg_generator import source_to_cfg
from semantics.forward import DefaultForwardSemantics
from visualization.graph_renderer import AnalysisResultRenderer


class TestIntervalStore(TestCase):
    def test_simple(self):
        name = 'simple'
        source = """a = 3 * (2+5)"""

        var_a = VariableIdentifier(int, 'a')
        variables = [var_a]
        cfg = source_to_cfg(source)
        forward_interpreter = ForwardInterpreter(cfg, DefaultForwardSemantics(), 3)
        result = forward_interpreter.analyze(ExpressionStore(variables))

        AnalysisResultRenderer().render((cfg, result), label=f"CFG with Results for {name}",
                                        filename=f"CFGR {name}",
                                        directory="graphs", view=False)

        result_store = result.get_node_result(cfg.nodes[2])[1]
        right_expr = result_store.variables[var_a]
        print(right_expr)

        store = IntervalStore(variables)
        interval = store.evaluate_expression(right_expr)
        print(interval)

        self.assertTupleEqual((interval.lower, interval.upper), (21, 21))
