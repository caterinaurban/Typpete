"""Inferrer for python statements.

Infers the types for the following expressions:
    - Assign(expr* targets, expr value)
    - Return(expr? value)
    - Delete(expr* targets)
    - If(expr test, stmt* body, stmt* orelse)
    - While(expr test, stmt* body, stmt* orelse)
    - For(expr target, expr iter, stmt* body, stmt* orelse)

    TODO:
    - AugAssign(expr target, operator op, expr value)
    - AnnAssign(expr target, expr annotation, expr? value, int simple)
    - AsyncFor(expr target, expr iter, stmt* body, stmt* orelse)
    - With(withitem* items, stmt* body)
    - AsyncWith(withitem* items, stmt* body)
    - Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
    - Import(alias* names)
    - ImportFrom(identifier? module, alias* names, int? level)
    - Global(identifier* names)
    - Nonlocal(identifier* names)
"""

import expr_inferrer as expr, ast
from context import Context
from i_types import *

def __infer_assignment_target(target, context, value_type):
    """Infer the type of a target in an assignment

    Attributes:
        target: the target whose type is to be inferred
        context: the current context level
        value_type: the type of the value assigned to the target

    Target cases:
        - Variable name. Ex: x = 1
        - Tuple. Ex: a, b = 1, "string"
        - List. Ex: [a, b] = [1, "string"]
        - Subscript. Ex: x[0] = 1, x[1 : 2] = [2,3], x["key"] = value
        - Compound: Ex: a, b[0], [c, d], e["key"] = 1, 2.0, [True, False], "value"

    Limitation:
        - In case of tuple/list assignments, there are no guarantees for correct number of unpacked values.
            Because the length of the list/tuple may not be resolved statically.
    TODO: Attributes assignment
    """
    if isinstance(target, ast.Name):
        if context.has_variable(target.id): # Check if variable is already inferred before
            var_type = context.get_type(target.id)
            if var_type.is_subtype(value_type):
                context.set_type(target.id, value_type)
            elif not value_type.is_subtype(var_type):
                raise TypeError("The type of {} is {}. Cannot assign it to {}.".format(target.id,
                                                                                    var_type.get_name(),
                                                                                    value_type.get_name()))
        else:
            context.set_type(target.id, value_type)
    elif isinstance(target, ast.Tuple) or isinstance(target, ast.List): # Tuple/List assignment
        if not expr.is_sequence(value_type):
            raise ValueError("Cannot unpack a non sequence.")
        for i in range(len(target.elts)):
            seq_elem = target.elts[i]
            if isinstance(value_type, TString):
                __infer_assignment_target(seq_elem, context, value_type)
            elif isinstance(value_type, TList):
                __infer_assignment_target(seq_elem, context, value_type.type)
            elif isinstance(value_type, TTuple):
                __infer_assignment_target(seq_elem, context, value_type.types[i])
    elif isinstance(target, ast.Subscript): # Subscript assignment
        subscript_type = expr.infer(target, context)
        indexed_type = expr.infer(target.value, context)
        if isinstance(indexed_type, TString):
            raise TypeError("String objects don't support item assignment.")
        elif isinstance(indexed_type, TTuple):
            raise TypeError("Tuple objects don't support item assignment.")
        elif isinstance(indexed_type, TList):
            if isinstance(target.slice, ast.Index):
                if indexed_type.type.is_subtype(value_type): # Update the type of the list with the more generic type
                    if isinstance(target.value, ast.Name):
                        context.set_type(target.value.id, TList(value_type))
                elif not value_type.is_subtype(indexed_type.type):
                    raise TypeError("Cannot assign {} to {}.".format(value_type.get_name(), indexed_type.type.get_name()))
            else: # Slice subscripting
                if indexed_type.is_subtype(value_type):
                    if isinstance(target.value, ast.Name): # Update the type of the list with the more generic type
                        context.set_type(target.value.id, value_type)
                elif not (isinstance(value_type, TList) and value_type.type.is_subtype(indexed_type.type)):
                    raise TypeError("Cannot assign {} to {}.".format(value_type.get_name(), indexed_type.get_name()))
        elif isinstance(indexed_type, TDictionary):
            if indexed_type.value_type.is_subtype(value_type):
                if isinstance(target.value, ast.Name): # Update the type of the dictionary values with the more generic type
                    context.get_type(target.value.id).value_type = value_type
            elif not value_type.is_subtype(indexed_type.value_type):
                raise TypeError("Cannot assign {} to a dictionary item of type {}.".format(value_type.get_name(), indexed_type.value_type.get_name()))
        else:
            raise NotImplementedError("The inference for {} subscripting is not supported.".format(indexed_type.get_name()))
    else:
        raise NotImplementedError("The inference for {} assignment is not supported.".format(type(target).__name__))

def _infer_assign(node, context):
    """Infer the types of target variables in an assignment node."""
    value_type = expr.infer(node.value, context) # The type of the value assigned to the targets in the assignment statement.
    for target in node.targets:
        __infer_assignment_target(target, context, value_type)

    return TNone()

def __delete_element(target, context):
    """Remove (if needed) a target from the context

    Cases:
        - del var_name: remove its type mappingfrom the context directly.
        - del subscript:
                    * Tuple/String --> Immutable. Raise exception.
                    * List/Dict --> Do nothing to the context.
    TODO: Attribute deletion
    """
    if isinstance(target, (ast.Tuple, ast.List)): # Multiple deletions
        for elem in target.elts:
            __delete_element(elem, context)
    elif isinstance(target, ast.Name):
        context.delete_type(target.id)
    elif isinstance(target, ast.Subscript):
        indexed_type = expr.infer(target.value)
        if isinstance(indexed_type, TString):
            raise TypeError("String objects don't support item deletion.")
        elif isinstance(indexed_type, TTuple):
            raise TypeError("Tuple objects don't support item deletion.")

def _infer_delete(node, context):
    """Remove (if needed) the type of the deleted items in the current context"""
    for target in node.targets:
        __delete_element(target, context)

    return TNone()

def __infer_body(body, context):
    """Infer the type of a code block containing multiple statements"""
    body_type = TNone()
    for stmt in body:
        stmt_type = infer(stmt, context)
        if body_type.is_subtype(stmt_type):
            body_type = stmt_type
        elif not stmt_type.is_subtype(body_type):
            if isinstance(body_type, UnionTypes):
                body_type.union(stmt_type)
            elif isinstance(stmt_type, UnionTypes):
                stmt_type.union(body_type)
                body_type = stmt_type
            else:
                union = {body_type, stmt_type}
                body_type = UnionTypes(union)
    return body_type

def _infer_control_flow(node, context):
    """Infer the type(s) for an if/while/for statements block.

    Arguments:
        node: The AST node to be inferred
        context: the current context level
    Example:
        if (some_condition):
            ......
            return "some string"
        else:
            ......
            return 2.0

        type: Union{String, Float}
    """
    body_type = __infer_body(node.body, context)
    else_type = __infer_body(node.orelse, context)

    if body_type.is_subtype(else_type):
        return else_type
    elif else_type.is_subtype(body_type):
        return body_type

    if isinstance(body_type, UnionTypes):
        body_type.union(else_type)
        return body_type
    elif isinstance(else_type, UnionTypes):
        else_type.union(body_type)
        return else_type
    return UnionTypes({body_type, else_type})

def _infer_for(node, context):
    """Infer the type for a for loop node

    Limitation:
        - The iterable should only be a set, a list or an iterator (not a tuple or a dict).
            For example: the following is not allowed:
                for x in (1, 2.0, "string"):
                    ....
    """
    iter_type = expr.infer(node.iter, context)
    if not isinstance(iter_type, (TList, TSet, TIterator)):
        raise TypeError("The iterable should only be a set, list or iterator. Found {}.".format(iter_type.get_name()))

    # Infer the target in the loop, inside the global context
    # Cases:
    # - Var name. Ex: for i in range(5)..
    # - Tuple. Ex: for (a,b) in [(1,"st"), (3,"st2")]..
    # -List. Ex: for [a,b] in [(1, "st"), (3, "st2")]..
    __infer_assignment_target(node.target, context, iter_type.type)

    return _infer_control_flow(node, context)


def infer(node, context):
    if isinstance(node, ast.Assign):
        return _infer_assign(node, context)
    elif isinstance(node, ast.Return):
        return expr.infer(node.value, context)
    elif isinstance(node, ast.Delete):
        return _infer_delete(node, context)
    elif isinstance(node, (ast.If, ast.While)):
        return _infer_control_flow(node, context)
    elif isinstance(node, ast.For):
        return _infer_for(node, context)
    return TNone()
