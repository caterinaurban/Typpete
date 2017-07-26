from abstract_domains.state import State
from collections import deque
from copy import deepcopy
from core.cfg import Basic, Loop, Conditional, ControlFlowGraph, Edge
from engine.interpreter import Interpreter
from engine.result import AnalysisResult
from semantics.backward import BackwardSemantics
from queue import Queue


class BackwardInterpreter(Interpreter):
    def __init__(self, cfg: ControlFlowGraph, semantics: BackwardSemantics, widening: int):
        """Backward control flow graph interpreter.

        :param cfg: control flow graph to analyze
        :param widening: number of iterations before widening 
        """
        super().__init__(cfg, semantics, widening)

    @property
    def semantics(self):
        return self._semantics

    def analyze(self, initial: State) -> AnalysisResult:

        # prepare the worklist and iteration counts
        worklist = Queue()
        worklist.put(self.cfg.out_node)
        iterations = {node: 0 for node in self.cfg.nodes}

        while not worklist.empty():
            current = worklist.get()  # retrieve the current node

            iteration = iterations[current.identifier]

            # retrieve the previous exit state of the node
            if current in self.result.result:
                previous = deepcopy(self.result.get_node_result(current)[-1])
            else:
                previous = None

            # compute the current exit state of the current node
            entry = deepcopy(initial)
            if current.identifier != self.cfg.out_node.identifier:
                entry.bottom()
                # join incoming states
                edges = self.cfg.out_edges(current)
                for edge in edges:
                    if edge.target in self.result.result:
                        successor = deepcopy(self.result.get_node_result(edge.target)[0])
                    else:
                        successor = deepcopy(initial).bottom()
                    # handle non-default edges
                    if edge.kind == Edge.Kind.IF_IN:
                        successor = successor.exit_if()
                    elif edge.kind == Edge.Kind.IF_OUT:
                        successor = successor.enter_if()
                    elif edge.kind == Edge.Kind.LOOP_IN:
                        successor = successor.exit_loop()
                    elif edge.kind == Edge.Kind.LOOP_OUT:
                        successor = successor.enter_loop()
                    # handle conditional edges
                    if isinstance(edge, Conditional):
                        successor = self.semantics.semantics(edge.condition, successor).filter()
                    entry = entry.join(successor)
                # widening
                if isinstance(current, Loop) and self.widening < iteration:
                    entry = deepcopy(previous).widening(entry)

            # check for termination and execute block
            if previous is None or not entry.less_equal(previous):
                states = deque([entry])
                if isinstance(current, Basic):
                    successor = entry
                    for stmt in reversed(current.stmts):
                        successor = self.semantics.semantics(stmt, deepcopy(successor))
                        states.appendleft(successor)
                elif isinstance(current, Loop):
                    # nothing to be done
                    pass
                self.result.set_node_result(current, list(states))
                # update worklist and iteration count
                for node in self.cfg.predecessors(current):
                    worklist.put(node)
                iterations[current.identifier] = iteration + 1

        return self.result
