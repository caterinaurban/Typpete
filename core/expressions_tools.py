from copy import deepcopy
from functools import reduce

from core.expressions import Expression, UnaryBooleanOperation, BinaryBooleanOperation, BinaryComparisonOperation, \
    BinaryArithmeticOperation, Literal, VariableIdentifier, UnaryArithmeticOperation


def iter_fields(expr: Expression):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``expr._fields``
    that is present on *expr*.
    """
    for name, field in expr.__dict__.items():
        yield name, field


def iter_child_exprs(expr: Expression):
    """
    Yield all direct child expressions of *expr*, that is, all fields that are expressions
    and all items of fields that are lists of expressions.
    """
    for _, field in iter_fields(expr):
        if isinstance(field, Expression):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, Expression):
                    yield item


def walk(expr: Expression):
    """
    Recursively yield all descendant expressions in the tree starting at *expr*
    (including *expr* itself), in no specified order.  This is useful if you
    only want to modify expressions in place and don't care about the context.
    """
    from collections import deque
    todo = deque([expr])
    while todo:
        expr = todo.popleft()
        todo.extend(iter_child_exprs(expr))
        yield expr


class ExpressionVisitor:
    """
    An expression visitor base class that walks the expression tree and calls a
    visitor function for every expression found.  This function may return a value
    which is forwarded by the `visit` method.

    This class is meant to be subclassed, with the subclass adding visitor
    methods.

    Per default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node.  So a `TryFinally` node visit function would
    be `visit_TryFinally`.  This behavior can be changed by overriding
    the `visit` method.  If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.

    Don't use the `NodeVisitor` if you want to apply changes to expression during
    traversing.  For this a special visitor exists (`ExpressionTransformer`) that
    allows modifications.
    
    Adopted from `ast.py`.
    """

    def visit(self, expr, *args, **kwargs):
        """Visit an expression."""
        method = 'visit_' + expr.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(expr, *args, **kwargs)

    def generic_visit(self, expr, *args, **kwargs):
        """Called if no explicit visitor function exists for an expression."""
        last_result = None
        for name, field in iter_fields(expr):
            if isinstance(field, Expression):
                last_result = self.visit(field, *args, **kwargs)
            elif isinstance(field, list):
                for item in field:
                    if isinstance(item, Expression):
                        last_result = self.visit(item, *args, **kwargs)
        return last_result


class ExpressionTransformer(ExpressionVisitor):
    """
    A :class:`ExpressionVisitor` subclass that walks the abstract syntax tree and
    allows modification of expressions.

    The `ExpressionTransformer` will walk the expression tree and use the return value of the
    visitor methods to replace or remove the old node.  If the return value of
    the visitor method is ``None``, the node will be removed from its location,
    otherwise it is replaced with the return value.  The return value may be the
    original node in which case no replacement takes place.

    Here is an example transformer that rewrites all occurrences of name lookups
    (``foo``) to ``data['foo']``::

       class RewriteName(ExpressionTransformer):

           def visit_Name(self, node):
               return copy_location(Subscript(
                   value=Name(id='data', ctx=Load()),
                   slice=Index(value=Str(s=node.id)),
                   ctx=node.ctx
               ), node)

    Keep in mind that if the expression you're operating on has child nodes you must
    either transform the child expressions yourself or call the :meth:`generic_visit`
    method for the expression first.

    For expressions that were part of a collection of expressions, the visitor may also return a list of expressions 
    rather than just a single expression. 

    Usually you use the transformer like this::

       node = YourTransformer().visit(node)
       
    Adopted from `ast.py`.
    """

    def generic_visit(self, expr, *args, **kwargs):
        for field, old_value in iter_fields(expr):
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, Expression):
                        value = self.visit(value, *args, **kwargs)
                        if value is None:
                            continue
                        elif not isinstance(value, Expression):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, Expression):
                new_node = self.visit(old_value, *args, **kwargs)
                if new_node is None:
                    delattr(expr, field)
                else:
                    setattr(expr, field, new_node)
        return expr


Sign = UnaryArithmeticOperation.Operator
PLUS = Sign.Add
MINUS = Sign.Sub


class SimplifierDetector(ExpressionVisitor):
    class Summands:
        def __init__(self):
            self.vars = []  # VariableIdentifier OR -VariableIdentifier
            self.constant = 0

        def combine(self, other):
            self.vars += other.vars
            self.constant += other.constant

        def to_expression(self):
            """Ejects this summands as valid expression tree."""

            def build_var_tree(x, y):
                return BinaryArithmeticOperation(int, x, BinaryArithmeticOperation.Operator.Add, y)

            if self.vars:
                expr = reduce(build_var_tree, self.vars)

                if self.constant != 0:
                    literal_expr = Literal(int, str(abs(self.constant)))
                    op = BinaryArithmeticOperation.Operator.Sub if self.constant < 0 else BinaryArithmeticOperation.Operator.Add
                    expr = BinaryArithmeticOperation(int, expr, op, literal_expr)
            elif self.constant != 0:
                expr = Literal(int, str(abs(self.constant)))
                if self.constant < 0:
                    expr = UnaryArithmeticOperation(int, UnaryArithmeticOperation.Operator.Sub, expr)
            else:
                raise ValueError("Neither summands nor constant present: can not create expression!")
            return expr

    def visit_Literal(self, expr: Literal, invert=False):
        s = SimplifierDetector.Summands()
        s.constant = int(expr.val)
        if invert:
            s.constant = - s.constant
        return s

    def visit_VariableIdentifier(self, expr: VariableIdentifier, invert=False):
        s = SimplifierDetector.Summands()
        if invert:
            s.vars.append(UnaryArithmeticOperation(int, UnaryArithmeticOperation.Operator.Sub, expr))
        else:
            s.vars.append(expr)
        return s

    def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation, invert=False):
        s = self.visit(expr.expression, invert=(expr.operator == UnaryArithmeticOperation.Operator.Sub) != invert)
        if s:
            expr.summands = s
        return s

    def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation, invert=False):
        if expr.operator in [BinaryArithmeticOperation.Operator.Add, BinaryArithmeticOperation.Operator.Sub]:
            left_summands = self.visit(expr.left, invert=invert)
            right_summands = self.visit(expr.right,
                                        invert=(expr.operator == BinaryArithmeticOperation.Operator.Sub) != invert)
            if left_summands and right_summands:
                left_summands.combine(right_summands)
                expr.summands = left_summands
                return left_summands
            else:
                return None
        else:
            return None

    def generic_visit(self, expr, invert=False):
        super().generic_visit(expr, invert)
        return None  # default case is not returning a Summands instance, signaling that this expr can not be simplified


class SimplifierTransformer(ExpressionTransformer):
    def visit_UnaryArithmeticOperation(self, expr: UnaryArithmeticOperation):
        if hasattr(expr, 'summands'):
            return expr.summands.to_expression()
        else:
            self.generic_visit(expr.expression)

    def visit_BinaryArithmeticOperation(self, expr: BinaryArithmeticOperation):
        if hasattr(expr, 'summands'):
            return expr.summands.to_expression()
        else:
            self.generic_visit(expr.left)
            self.generic_visit(expr.right)


def simplify(expr: Expression):
    SimplifierDetector().visit(expr)
    return SimplifierTransformer().visit(expr)


class NotFreeConditionTransformer(ExpressionTransformer):
    """Transforms an expression by pushing ``not``-operators down the expression tree and reversing binary operations

    Uses De-Morgans law to push down ``not``-operators. Finally gets rid of all ``not``-operators, by reversing 
    binary comparison operators that are negated. 
    """

    def visit_UnaryBooleanOperation(self, expr: UnaryBooleanOperation, invert=False):
        if expr.operator == UnaryBooleanOperation.Operator.Neg:
            return self.generic_visit(expr.expression, invert=not invert)  # double inversion cancels itself
        else:
            raise NotImplementedError()

    def visit_BinaryBooleanOperation(self, expr: BinaryBooleanOperation, invert=False):
        if invert:
            if expr.operator == BinaryBooleanOperation.Operator.And:
                return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left, invert=True),
                                              BinaryBooleanOperation.Operator.Or,
                                              self.generic_visit(expr.right, invert=True))
            elif expr.operator == BinaryBooleanOperation.Operator.Or:
                return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left, invert=True),
                                              BinaryBooleanOperation.Operator.And,
                                              self.generic_visit(expr.right, invert=True))
            elif expr.operator == BinaryBooleanOperation.Operator.Xor:
                # use not(a xor b) == (a and b) or (not(a) and not(b))
                cond_both = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=False),
                                                   BinaryBooleanOperation.Operator.And,
                                                   self.generic_visit(deepcopy(expr.right), invert=False))
                cond_none = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=True),
                                                   BinaryBooleanOperation.Operator.And,
                                                   self.generic_visit(deepcopy(expr.right), invert=True))
                return BinaryBooleanOperation(expr.typ, cond_both,
                                              BinaryBooleanOperation.Operator.Or,
                                              cond_none)
        else:
            # get rid of xor also if not inverted!
            if expr.operator == BinaryBooleanOperation.Operator.Xor:
                # use a xor b == (a or b) and not(a and b) == (a or b) and (not(a) or not(b))
                cond_one = BinaryBooleanOperation(expr.typ, self.generic_visit(deepcopy(expr.left), invert=False),
                                                  BinaryBooleanOperation.Operator.Or,
                                                  self.generic_visit(deepcopy(expr.right), invert=False))
                cond_not_both = BinaryBooleanOperation(expr.typ,
                                                       self.generic_visit(deepcopy(expr.left), invert=True),
                                                       BinaryBooleanOperation.Operator.Or,
                                                       self.generic_visit(deepcopy(expr.right), invert=True))
                return BinaryBooleanOperation(expr.typ, cond_one, BinaryBooleanOperation.Operator.And,
                                              cond_not_both)
            else:
                return BinaryBooleanOperation(expr.typ, self.generic_visit(expr.left),
                                              expr.operator,
                                              self.generic_visit(expr.right))

    def visit_BinaryComparisonOperation(self, expr: BinaryComparisonOperation, invert=False):
        return BinaryComparisonOperation(expr.typ, self.generic_visit(expr.left),
                                         expr.operator.reverse_operator() if invert else expr.operator,
                                         self.generic_visit(expr.right))


def make_condition_not_free(expr: Expression):
    return NotFreeConditionTransformer().visit(expr)
