"""Types predicates used throughout the project"""

from i_types import *

def is_sequence(t):
	return isinstance(t, (TList, TTuple, TString, TBytesString))

def can_be_indexed(t):
    return is_sequence(t) or isinstance(t, TDictionary)

def has_supertype(types, t):
    """Return true if (t) is a subtype of any of the types in (types)"""
    for ti in types:
        if t.is_subtype(ti):
            return True
    return False

def satisfies_predicates(t, *preds):
    """Check if type t satisfies any of the predicates preds"""
    for pred in preds:
        if pred(t):
            return True
    return False

def is_numeric(t):
	return t.is_subtype(TFloat())
