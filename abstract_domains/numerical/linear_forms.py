from collections import namedtuple

from abstract_domains.numerical.interval import IntervalLattice
from core.expressions import *

from core.expressions_tools import ExpressionVisitor

Sign = UnaryArithmeticOperation.Operator
PLUS = Sign.Add
MINUS = Sign.Sub


class InvalidFormError(ValueError):
    pass


class LinearForm(ExpressionVisitor):
    """Holds an expression in linear form with one or several variables: `+/- var1 +/- var2 + ... + interval`."""

    def __init__(self, expr: Expression):
        """Initializes this instance with the linear form of an expression.

        If possible, this instance holds the parts of the linear form separately. If not possible to 
        construct this form, this raises a InvalidFormError.
        """
        self._var_summands = {}  # dictionary holding {var: sign}
        self._interval = None

        self.visit(expr)

    @property
    def var_summands(self):
        return self._var_summands

    def _encounter_new_var(self, var, sign=PLUS):
        if var in self.var_summands:
            raise InvalidFormError(f"VariableIdentifier {var} appears twice!")
        self.var_summands[var] = sign

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        if self._interval:
            raise InvalidFormError("interval set twice (is immutable)!")
        self._interval = value

    def __str__(self):
        vars_string = ' '.join([f"{str(sign)} {var}" for var, sign in self.var_summands.items()])
        return vars_string + (f" + {self._interval}" if self._interval else "")

    # the visit methods should either set parts of the linear form or call visit method on children, propagating if
    # the sub-expressions is negated. They can also fallback on other visitors like the interval visitor via
    # IntervalLattice.evaluate(expr)

    def visit_Literal(self, expr: Literal, invert=False):
        self.interval = IntervalLattice.evaluate(expr)
        if invert:
            self.interval.negate()

    def visit_VariableIdentifier(self, expr: VariableIdentifier, invert=False):
        self._encounter_new_var(expr, sign=MINUS if invert else PLUS)

    def visit_Input(self, expr: Input, invert=False):
        self.interval = IntervalLattice().top()
        if invert:
            self.interval.negate()

    def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation, invert=False):
        # we have to check if binary operation can be reordered to correspond to valid formats:
        # +/- var + interval
        # OR
        # +/- var1 +/- var2

        try:
            # just try if interval lattice is capable of reducing to single interval (if no vars inside expr)
            self.interval = IntervalLattice.evaluate(expr.left)
            if invert:
                self.interval.negate()
        except ValueError:
            self.visit(expr.left, invert=invert)

        if expr.operator not in [BinaryArithmeticOperation.Operator.Add, BinaryArithmeticOperation.Operator.Sub]:
            raise InvalidFormError("Unsupported binary arithmetic operator")

        try:
            # just try if interval lattice is capable of reducing to single interval (if no vars inside expr)
            self.interval = IntervalLattice.evaluate(expr.right)
            if (expr.operator == BinaryArithmeticOperation.Operator.Sub) != invert:
                self.interval.negate()
        except ValueError:
            self.visit(expr.right, invert=(expr.operator == BinaryArithmeticOperation.Operator.Sub) != invert)

    def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation, invert=False):
        if expr.operator == UnaryArithmeticOperation.Operator.Add:
            self.visit(expr.expression, invert=invert)
        elif expr.operator == UnaryArithmeticOperation.Operator.Sub:
            self.visit(expr.expression, invert=not invert)
        else:
            raise ValueError("Unknown operator")

    def generic_visit(self, expr, *args, **kwargs):
        raise InvalidFormError(
            f"{type(self)} does not support generic visit of expressions! Define handling for expression {type(expr)} explicitly!")


class SingleVarLinearForm(LinearForm):
    """Holds an expression in linear form with a single variable: `+/- var + interval`."""

    def __init__(self, expr: Expression):
        """Initializes this instance with the single variable form of an expression.

        If possible, this instance holds the parts of the single variable linear form separately. If not possible to 
        construct this form, this raises a InvalidFormError.
        """

        super().__init__(expr)

        if len(self.var_summands) > 1:
            raise InvalidFormError("More than a single variable detected!")

        # extract single var information from inherited, more complex data-structure
        self._var_sign = list(self.var_summands.values())[0] if self.var_summands else PLUS
        self._var = list(self.var_summands.keys())[0] if self.var_summands else None

    @property
    def var_sign(self):
        return self._var_sign

    @property
    def var(self):
        return self._var
