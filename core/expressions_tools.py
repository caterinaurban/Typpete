from core.expressions import Expression


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
        for name, field in iter_fields(expr):
            if isinstance(field, Expression):
                self.visit(field, *args, **kwargs)
            elif isinstance(field, list):
                for item in field:
                    if isinstance(item, Expression):
                        yield item


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
