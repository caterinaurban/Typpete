"""Stub file for methods invoked on sets"""
from typing import TypeVar, Set

TSet = TypeVar("TSet")


def add(s: Set[TSet], e: TSet) -> None:
    """Add the element `e` to the set `s`"""
    pass


def union(s: Set[TSet], t: Set[TSet]) -> Set[TSet]:
    """Return a new set with elements from both `s` and `t`"""
    pass