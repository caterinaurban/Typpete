from collections import deque
from copy import deepcopy
from core.cfg import Basic, Loop, Conditional, ControlFlowGraph
from engine.interpreter import Interpreter
from queue import Queue
from engine.result import AnalysisResult
from abstract_domains.state import State


class ForwardInterpreter(Interpreter):
    def __init__(self, cfg: ControlFlowGraph, widening: int):
        """Forward analysis runner.

        :param cfg: control flow graph to analyze 
        :param widening: number of iterations before widening 
        """
        super().__init__(cfg, widening)

    def analyze(self, initial: State) -> AnalysisResult:

        # prepare the worklist and iteration counts
        worklist = Queue()
        worklist.put(self.cfg.in_node)
        iterations = {node: 0 for node in self.cfg.nodes}

        while not worklist.empty():
            current = worklist.get()        # retrieve the current node
            iteration = iterations[current.identifier]

            # retrieve the previous entry state of the node
            if current.identifier in self.result.result:
                previous = deepcopy(self.result.get_node_result(current)[0])
            else:
                previous = deepcopy(initial).bottom()

            # compute the current entry state of the current node
            entry = deepcopy(initial)
            if current.identifier != self.cfg.in_node.identifier:
                entry = entry.bottom()
                # join incoming states
                edges = self.cfg.in_edges(current)
                for edge in edges:
                    predecessor = deepcopy(self.result.get_node_result(edge.source)[-1])
                    # handle conditional edges
                    if isinstance(edge, Conditional):
                        predecessor = edge.condition.forward_semantics(predecessor)
                    entry = entry.join(predecessor)
                # widening
                if isinstance(current, Loop) and self.widening < iteration:
                    entry = deepcopy(previous).widening(entry)

            # check for termination and execute block
            if not entry.less_equal(previous):
                states = deque([entry])
                if isinstance(current, Basic):
                    successor = entry
                    for stmt in current.stmts:
                        successor = stmt.forward_semantics(deepcopy(successor))
                        states.append(successor)
                elif isinstance(current, Loop):
                    # nothing to be done
                    pass
                self.result.set_node_result(current, list(states))
                # update worklist and iteration count
                for node in self.cfg.successors(current):
                    worklist.put(node)
                iterations[current.identifier] = iteration + 1

        return self.result
