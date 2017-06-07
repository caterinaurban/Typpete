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
    Yield all direct child exprs of *expr*, that is, all fields that are exprs
    and all items of fields that are lists of exprs.
    """
    for name, field in iter_fields(expr):
        if isinstance(field, Expression):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, Expression):
                    yield item


def walk(expr: Expression):
    """
    Recursively yield all descendant exprs in the tree starting at *expr*
    (including *expr* itself), in no specified order.  This is useful if you
    only want to modify exprs in place and don't care about the context.
    """
    from collections import deque
    todo = deque([expr])
    while todo:
        expr = todo.popleft()
        todo.extend(iter_child_exprs(expr))
        yield expr
