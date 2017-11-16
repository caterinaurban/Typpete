"""Stub file for methods invoked on lists"""
from typing import TypeVar, List

T = TypeVar("T")


def append(l: List[T], e: T) -> None:
    """Append a new element `e` to the list `l`
    
    Invoked on any list
    """
    pass


def count(l: List[T], e: T) -> int:
    """Return how many times element `e` appears in list `l`"""
    pass


def extend(l: List[T], l2: List[T]) -> None:
    """Append the contents of list `l2` to list `l`"""
    pass


def index(l: List[T], e: T) -> int:
    """Return the index of the first appearance of element `e` in list `l`"""
    pass


def insert(l: List[T], i: int, e: T) -> None:
    """Insert element `e` to the list `l` at index `i`"""
    pass


def pop(l: List[T]) -> T:
    """Delete an item from the list `l` at the index i"""
    pass


def remove(l: List[T], e: T) -> None:
    """Remove element `e` from the list `l`"""
    pass


def reverse(l: List[T]) -> None:
    """Reverse a list"""
    pass


def sort(l: List[T]) -> None:
    """Sort a list"""
    pass
