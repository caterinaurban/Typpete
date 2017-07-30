from typing import List, Set, Tuple, FrozenSet
from itertools import chain, combinations, product
from copy import deepcopy

from abstract_domains.lattice import BoundedLattice
from abstract_domains.state import State
from core.expressions import Expression, VariableIdentifier, UnaryBooleanOperation, Literal, BinaryBooleanOperation, \
    Input


class BoolTracesState(BoundedLattice, State):
    class BoolTrace:
        def __init__(self, values: Tuple):
            self._trace = [values]

        @property
        def trace(self):
            return self._trace

        @trace.setter
        def trace(self, trace):
            self._trace = trace

        def __eq__(self, other: 'BoolTracesState.BoolTrace'):
            if isinstance(other, self.__class__):
                return repr(self) == repr(other)
            return False

        def __hash__(self):
            return hash(repr(self))

        def __ne__(self, other: 'BoolTracesState.BoolTrace'):
            return not (self == other)

        def __repr__(self):
            return "".join("({})".format("".join(value for value in state)) for state in self.trace)

        def evaluate(self, variables: List[VariableIdentifier], exp: Expression) -> str:
            if isinstance(exp, Literal):
                if exp.val == 'True':
                    return 'T'
                else:
                    return 'F'
            elif isinstance(exp, VariableIdentifier):
                idx = variables.index(exp)
                return self.trace[0][idx]
            elif isinstance(exp, UnaryBooleanOperation):
                neg = self.evaluate(variables, exp.expression)
                if neg == 'T':
                    return 'F'
                else:
                    return 'T'
            elif isinstance(exp, BinaryBooleanOperation):
                left = self.evaluate(variables, exp.left)
                right = self.evaluate(variables, exp.right)
                if exp.operator is BinaryBooleanOperation.Operator.And:
                    if left == 'T' and right == 'T':
                        return 'T'
                    else:
                        return 'F'
                elif exp.operator is BinaryBooleanOperation.Operator.Or:
                    if left == 'T' or right == 'T':
                        return 'T'
                    else:
                        return 'F'
                else:
                    raise NotImplementedError("Expression evaluation for {} is not implemented!".format(exp))
            else:
                raise NotImplementedError("Expression evaluation for {} is not implemented!".format(exp))

        def test(self, idx: int, value: str) -> bool:
            return self.trace[0][idx] == value

        def replace(self, idx: int, value: str) -> 'BoolTracesState.BoolTrace':
            head = list(self.trace[0])
            head[idx] = value
            self.trace = [tuple(head)] + self.trace
            return self

        def variety(self, variables: List[VariableIdentifier], inputs: List[VariableIdentifier]) -> List[str]:
            value = list()
            for var in inputs:
                idx = variables.index(var)
                value.append(self.trace[0][idx])
            return value

    def __init__(self, variables: List[VariableIdentifier], hyper: bool = False):
        """Live/Dead variable analysis state representation.

        :param variables: list of program variables
        """
        super().__init__()
        self._variables = variables     # e.g., ['x', 'y']
        self._traces = frozenset(BoolTracesState.BoolTrace(t) for t in product(*[('T', 'F') for _ in variables]))
        # e.g., {[('T', 'T')], [('T', 'F')], [('F', 'T')], [('F', 'F')]}
        self._hyper = hyper
        t = len(self._traces)
        sets = frozenset(
            frozenset(t) for t in chain.from_iterable(combinations(self._traces, r) for r in range(t + 1))
        )
        self._sets = dict()
        i = 1
        for s in sets:
            self._sets[i] = s
            i = i + 1
        self._in = set()

    @property
    def variables(self):
        return self._variables

    @property
    def traces(self):
        return self._traces

    @traces.setter
    def traces(self, traces):
        self._traces = traces

    @property
    def hyper(self):
        return self._hyper

    @property
    def sets(self):
        return self._sets

    @sets.setter
    def sets(self, sets):
        self._sets = sets

    def __repr__(self):
        """Unambiguous string representing the current state.

        :return: unambiguous representation string
        """
        def trace_repr(s):
            return ", ".join(str(trace) for trace in s)

        def variety(s):
            if self._in and s:
                varieties = [(x, self._variety(s, x)) for x in self._in]
                values = set()
                for trace in s:
                    values.add(tuple(trace.variety(self.variables, self._in)))
                count = len(values)
                return " variety: " + " ".join(str(x) + "=" + str(v) for (x, v) in varieties) + " count: " + str(count)
            else:
                return ""

        def var_repr():
            return ", ".join(str(x) for x in self.variables)

        if self.hyper:
            sets = list(self.sets.values())
            List.sort(sets, key=lambda x: len(x), reverse=True)
            s1 = frozenset()
            s2 = frozenset()
            for el in sets:
                if el and s1.issubset(el):
                    s1 = el
                elif el and (not el.issubset(s1)) and s2.issubset(el):
                    s2 = el
                else:
                    pass
            return var_repr() + " {" + trace_repr(s1) + variety(s1) + "}\n{" + trace_repr(s2) + variety(s2) + "}"
            # return "{" + "}\n{".join(
            #     str(k) + ":\t" + trace_repr(s) + variety_repr(s) for k, s in self.sets.items() if s
            # ) + "}"
        else:
            return ", ".join(str(trace) for trace in self.traces)

    def _less_equal(self, other: 'BoolTracesState') -> bool:
        if self.hyper:
            subset = True
            for key in self.sets:
                subset = subset and self.sets[key].issubset(other.sets[key])
            return subset
        else:
            return self.traces.issubset(other.traces)

    def _join(self, other: 'BoolTracesState') -> 'BoolTracesState':
        if self.hyper:
            self._in = self._in.union(other._in)
            for key in self.sets:
                self.sets[key] = self.sets[key].union(other.sets[key])
        else:
            self.traces = self.traces.union(other.traces)
        return self

    def _widening(self, other: 'BoolTracesState'):
        return self._join(other)

    def _meet(self, other: 'BoolTracesState'):
        if self.hyper:
            self._in = self._in.intersection(other._in)
            for key in self.sets:
                self.sets[key] = self.sets[key].intersection(other.sets[key])
        else:
            self.traces = self.traces.intersection(other.traces)
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'BoolTracesState':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume_aux(self, traces: FrozenSet[BoolTrace], condition: Expression) -> FrozenSet[BoolTrace]:
        if isinstance(condition, VariableIdentifier):
            idx = self.variables.index(condition)
            result = set()
            for trace in traces:
                if trace.test(idx, 'T'):
                    result.add(deepcopy(trace))
            return frozenset(result)
        elif isinstance(condition, UnaryBooleanOperation):
            if isinstance(condition.expression, VariableIdentifier):
                idx = self.variables.index(condition.expression)
                result = set()
                for trace in traces:
                    if trace.test(idx, 'F'):
                        result.add(deepcopy(trace))
                return frozenset(result)
            else:
                raise NotImplementedError("Assume for {} is not implemented!".format(condition))
        else:
            raise NotImplementedError("Assume for {} is not implemented!".format(condition))

    def _assume(self, condition: Expression) -> 'BoolTracesState':
        if self.hyper:
            for key in self.sets:
                self.sets[key] = self._assume_aux(self.sets[key], condition)
        else:
            self.traces = self._assume_aux(self.traces, condition)
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_loop(self):
        return self  # nothing to be done

    def exit_loop(self):
        return self  # nothing to be done

    def enter_if(self):
        return self  # nothing to be done

    def exit_if(self):
        return self  # nothing to be done

    def _output(self, output: Expression) -> 'BoolTracesState':
        if self.hyper:  # nothing to be done otherwise
            for key in self.sets:  # for all sets of traces...
                unique = True
                for identifier in output.ids():  # for each output...
                    unique = unique and self._variety(self.sets[key], identifier) == 1
                if not unique:
                    self.sets[key] = frozenset()
        return self

    def _substitute_variable_aux(self, traces: FrozenSet[BoolTrace], left, right) -> FrozenSet[BoolTrace]:
        if isinstance(left, VariableIdentifier):
            idx = self.variables.index(left)
            if isinstance(right, Input):
                self._in.add(left)
                result = set()
                for trace in traces:
                    result.add(deepcopy(trace))
                    # result.add(deepcopy(trace).replace(idx, 'T'))
                    # result.add(deepcopy(trace).replace(idx, 'F'))
                return frozenset(result)
            else:
                result = set()
                for trace in traces:
                    tt = deepcopy(trace).replace(idx, 'T')
                    if trace.test(idx, tt.evaluate(self.variables, right)):
                        result.add(tt)
                    ff = deepcopy(trace).replace(idx, 'F')
                    if trace.test(idx, ff.evaluate(self.variables, right)):
                        result.add(ff)
                return frozenset(result)
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))

    def _substitute_variable(self, left: Expression, right: Expression) -> 'BoolTracesState':
        if self.hyper:
            for key in self.sets:
                self.sets[key] = self._substitute_variable_aux(self.sets[key], left, right)
        else:
            self.traces = self._substitute_variable_aux(self.traces, left, right)
        return self

    def _variety(self, traces: FrozenSet[BoolTrace], identifier: Expression) -> int:
        values = set()
        for trace in traces:
            values.add(trace.evaluate(self.variables, identifier))
        return len(values)


class TvlTracesState(BoundedLattice, State):
    class TvlTrace:
        def __init__(self, values: Tuple):
            self._trace = [values]

        @property
        def trace(self):
            return self._trace

        @trace.setter
        def trace(self, trace):
            self._trace = trace

        def __eq__(self, other: 'TvlTracesState.TvlTrace'):
            if isinstance(other, self.__class__):
                return repr(self) == repr(other)
            return False

        def __hash__(self):
            return hash(repr(self))

        def __ne__(self, other: 'TvlTracesState.TvlTrace'):
            return not (self == other)

        def __repr__(self):
            return "".join("({})".format("".join(value for value in state)) for state in self.trace)

        def evaluate(self, variables: List[VariableIdentifier], exp: Expression) -> str:
            if isinstance(exp, Literal):
                if exp.val == 'True':
                    return 'T'
                elif exp.val == 'False':
                    return 'F'
                else:
                    return '?'
            elif isinstance(exp, VariableIdentifier):
                idx = variables.index(exp)
                return self.trace[0][idx]
            elif isinstance(exp, UnaryBooleanOperation):
                neg = self.evaluate(variables, exp.expression)
                if neg == 'T':
                    return 'F'
                elif neg == 'F':
                    return 'T'
                else:
                    return '?'
            elif isinstance(exp, BinaryBooleanOperation):
                left = self.evaluate(variables, exp.left)
                right = self.evaluate(variables, exp.right)
                if exp.operator is BinaryBooleanOperation.Operator.And:
                    if left == 'T' and right == 'T':
                        return 'T'
                    elif left == '?' or right == '?':
                        return '?'
                    else:
                        return 'F'
                elif exp.operator is BinaryBooleanOperation.Operator.Or:
                    if left == 'T' or right == 'T':
                        return 'T'
                    elif left == '?' or right == '?':
                        return '?'
                    else:
                        return 'F'
                else:
                    raise NotImplementedError("Expression evaluation for {} is not implemented!".format(exp))
            else:
                raise NotImplementedError("Expression evaluation for {} is not implemented!".format(exp))

        def test(self, idx: int, value: str) -> bool:
            return self.trace[0][idx] == value

        def replace(self, idx: int, value: str) -> 'TvlTracesState.TvlTrace':
            head = list(self.trace[0])
            head[idx] = value
            self.trace = [tuple(head)] + self.trace
            return self

        def variety(self, variables: List[VariableIdentifier], inputs: List[VariableIdentifier]) -> List[str]:
            value = list()
            for var in inputs:
                idx = variables.index(var)
                value.append(self.trace[0][idx])
            return value

    def __init__(self, variables: List[VariableIdentifier], hyper: bool = False):
        """Live/Dead variable analysis state representation.

        :param variables: list of program variables
        """
        super().__init__()
        self._variables = variables     # e.g., ['x', 'y']
        self._traces = frozenset(TvlTracesState.TvlTrace(t) for t in product(*[('T', '?', 'F') for _ in variables]))
        self._hyper = hyper
        t = len(self._traces)
        sets = frozenset(
            frozenset(t) for t in chain.from_iterable(combinations(self._traces, r) for r in range(t + 1))
        )
        self._sets = dict()
        i = 1
        for s in sets:
            self._sets[i] = s
            i = i + 1
        self._in = set()

    @property
    def variables(self):
        return self._variables

    @property
    def traces(self):
        return self._traces

    @traces.setter
    def traces(self, traces):
        self._traces = traces

    @property
    def hyper(self):
        return self._hyper

    @property
    def sets(self):
        return self._sets

    @sets.setter
    def sets(self, sets):
        self._sets = sets

    def __repr__(self):
        """Unambiguous string representing the current state.

        :return: unambiguous representation string
        """

        def trace_repr(s):
            return ", ".join(str(trace) for trace in s)

        def variety(s):
            if self._in and s:
                varieties = [(x, self._variety(s, x)) for x in self._in]
                values = set()
                for trace in s:
                    values.add(tuple(trace.variety(self.variables, self._in)))
                count = len(values)
                return " variety: " + " ".join(str(x) + "=" + str(v) for (x, v) in varieties) + " count: " + str(count)
            else:
                return ""

        def var_repr():
            return ", ".join(str(x) for x in self.variables)

        if self.hyper:
            sets = list(self.sets.values())
            List.sort(sets, key=lambda x: len(x), reverse=True)
            s1 = frozenset()
            s2 = frozenset()
            s3 = frozenset()
            for el in sets:
                if el and s1.issubset(el):
                    s1 = el
                elif el and (not el.issubset(s1)) and s2.issubset(el):
                    s2 = el
                elif el and (not el.issubset(s1)) and (not el.issubset(s2)) and s3.issubset(el):
                    s3 = el
                else:
                    pass
            fst = trace_repr(s1) + variety(s1)
            snd = trace_repr(s2) + variety(s2)
            trd = trace_repr(s3) + variety(s3)
            return var_repr() + " {" + fst + "}\n{" + snd + "}\n{" + trd + "}"
        else:
            return ", ".join(str(trace) for trace in self.traces)

    def _less_equal(self, other: 'TvlTracesState') -> bool:
        if self.hyper:
            subset = True
            for key in self.sets:
                subset = subset and self.sets[key].issubset(other.sets[key])
            return subset
        else:
            return self.traces.issubset(other.traces)

    def _join(self, other: 'TvlTracesState') -> 'TvlTracesState':
        if self.hyper:
            self._in = self._in.union(other._in)
            for key in self.sets:
                self.sets[key] = self.sets[key].union(other.sets[key])
        else:
            self.traces = self.traces.union(other.traces)
        return self

    def _widening(self, other: 'TvlTracesState'):
        return self._join(other)

    def _meet(self, other: 'TvlTracesState'):
        if self.hyper:
            self._in = self._in.intersection(other._in)
            for key in self.sets:
                self.sets[key] = self.sets[key].intersection(other.sets[key])
        else:
            self.traces = self.traces.intersection(other.traces)
        return self

    def _access_variable(self, variable: VariableIdentifier) -> Set[Expression]:
        return {variable}

    def _assign_variable(self, left: Expression, right: Expression) -> 'TvlTracesState':
        raise NotImplementedError("Variable assignment is not implemented!")

    def _assume_aux(self, traces: FrozenSet[TvlTrace], condition: Expression) -> FrozenSet[TvlTrace]:
        if isinstance(condition, VariableIdentifier):
            idx = self.variables.index(condition)
            result = set()
            for trace in traces:
                if trace.test(idx, 'T'):
                    result.add(deepcopy(trace))
            return frozenset(result)
        elif isinstance(condition, UnaryBooleanOperation):
            if isinstance(condition.expression, VariableIdentifier):
                idx = self.variables.index(condition.expression)
                result = set()
                for trace in traces:
                    if trace.test(idx, 'F') or trace.test(idx, '?'):
                        result.add(deepcopy(trace))
                return frozenset(result)
            else:
                raise NotImplementedError("Assume for {} is not implemented!".format(condition))
        else:
            raise NotImplementedError("Assume for {} is not implemented!".format(condition))

    def _assume(self, condition: Expression) -> 'TvlTracesState':
        if self.hyper:
            for key in self.sets:
                self.sets[key] = self._assume_aux(self.sets[key], condition)
        else:
            self.traces = self._assume_aux(self.traces, condition)
        return self

    def _evaluate_literal(self, literal: Expression) -> Set[Expression]:
        return {literal}

    def enter_loop(self):
        return self  # nothing to be done

    def exit_loop(self):
        return self  # nothing to be done

    def enter_if(self):
        return self  # nothing to be done

    def exit_if(self):
        return self  # nothing to be done

    def _output(self, output: Expression) -> 'TvlTracesState':
        if self.hyper:  # nothing to be done otherwise
            for key in self.sets:  # for all sets of traces...
                unique = True
                for identifier in output.ids():  # for each output...
                    unique = unique and self._variety(self.sets[key], identifier) == 1
                if not unique:
                    self.sets[key] = frozenset()
        return self

    def _substitute_variable_aux(self, traces: FrozenSet[TvlTrace], left, right) -> FrozenSet[TvlTrace]:
        if isinstance(left, VariableIdentifier):
            idx = self.variables.index(left)
            if isinstance(right, Input):
                self._in.add(left)
                result = set()
                for trace in traces:
                    result.add(deepcopy(trace))
                    # result.add(deepcopy(trace).replace(idx, 'T'))
                    # result.add(deepcopy(trace).replace(idx, 'F'))
                return frozenset(result)
            else:
                result = set()
                for trace in traces:
                    tt = deepcopy(trace).replace(idx, 'T')
                    if trace.test(idx, tt.evaluate(self.variables, right)):
                        result.add(tt)
                    uu = deepcopy(trace).replace(idx, '?')
                    if trace.test(idx, uu.evaluate(self.variables, right)):
                        result.add(uu)
                    ff = deepcopy(trace).replace(idx, 'F')
                    if trace.test(idx, ff.evaluate(self.variables, right)):
                        result.add(ff)
                return frozenset(result)
        else:
            raise NotImplementedError("Variable substitution for {} is not implemented!".format(left))

    def _substitute_variable(self, left: Expression, right: Expression) -> 'TvlTracesState':
        if self.hyper:
            for key in self.sets:
                self.sets[key] = self._substitute_variable_aux(self.sets[key], left, right)
        else:
            self.traces = self._substitute_variable_aux(self.traces, left, right)
        return self

    def _variety(self, traces: FrozenSet[TvlTrace], identifier: Expression) -> int:
        values = set()
        for trace in traces:
            values.add(trace.evaluate(self.variables, identifier))
        if 'T' in values:
            pass
        return len(values)
