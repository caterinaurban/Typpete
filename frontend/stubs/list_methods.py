"""Stub file for methods invoked on lists"""
from typing import TypeVar, List, Generic

TT = TypeVar("TT")



def append(self: List[TT], e: TT) -> None:
    """Append a new element `e` to the list `l`
    
    Invoked on any list
    """
    pass


def count(self: List[TT], e: TT) -> int:
    """Return how many times element `e` appears in list `l`"""
    pass


def extend(self: List[TT], l2: List[TT]) -> None:
    """Append the contents of list `l2` to list `l`"""
    pass


def index(self: List[TT], e: TT) -> int:
    """Return the index of the first appearance of element `e` in list `l`"""
    pass


def insert(self: List[TT], i: int, e: TT) -> None:
    """Insert element `e` to the list `l` at index `i`"""
    pass


def pop(self: List[TT]) -> TT:
    """Delete an item from the list `l` at the index i"""
    pass


def remove(self: List[TT], e: TT) -> None:
    """Remove element `e` from the list `l`"""
    pass


def reverse(self: List[TT]) -> None:
    """Reverse a list"""
    pass


def sort(self: List[TT]) -> None:
    """Sort a list"""
    pass
