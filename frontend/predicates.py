"""Types predicates used throughout the project"""

from frontend.i_types import *


def is_sequence(t):
    return isinstance(t, TSequence)


def has_sequence(types):
    if is_sequence(types):
        return True
    if not isinstance(types, UnionTypes):
        return False
    for ti in types.types:
        if is_sequence(ti):
            return True
    return False


def has_instance(types, cl):
    if isinstance(types, cl):
        return True
    if not isinstance(types, UnionTypes):
        return False
    for ti in types.types:
        if isinstance(ti, cl):
            return True
    return False


def all_instance(types, cl):
    if isinstance(types, cl):
        return True
    if not isinstance(types, UnionTypes):
        return False
    for ti in types.types:
        if not isinstance(ti, cl):
            return False
    return True


def can_be_indexed(t):
    return has_sequence(t) or has_instance(t, TDictionary)


def has_supertype(types, t):
    """Return true if (t) is a subtype of any of the union type in (types)"""
    if t.is_subtype(types):
        return True
    if not isinstance(types, UnionTypes):
        return False
    for ti in types.types:
        if t.is_subtype(ti):
            return True
    return False


def has_subtype(types, t):
    """Return true if (t) is a supertype of any of the types in (types)"""
    if types.is_subtype(t):
        return True
    if not isinstance(types, UnionTypes):
        return False
    for ti in types.types:
        if ti.is_subtype(t):
            return True
    return False


def satisfies_predicates(t, *preds):
    """Check if type t satisfies any of the predicates preds"""
    for pred in preds:
        if pred(t):
            return True
    return False


def is_numeric(t):
    return isinstance(t, TNumber)
