"""Stub file for methods invoked on sets"""
from typing import TypeVar, Set

T = TypeVar("T")


def add(s: Set[T], e: T) -> None:
    """Add the element `e` to the set `s`"""
    pass


def union(s: Set[T], t: Set[T]) -> Set[T]:
    """Return a new set with elements from both `s` and `t`"""
    pass