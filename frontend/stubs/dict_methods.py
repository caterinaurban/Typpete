"""Stub file for methods invoked on lists"""
from typing import TypeVar, Dict, List, Tuple

T = TypeVar("T")
U = TypeVar("U")


def clear(dict: Dict[T, U]) -> None:
    """Removes all elements of dictionary dict"""
    pass


def copy(dict: Dict[T, U]) -> Dict[T, U]:
    """Returns a shallow copy of dictionary dict"""
    pass


def get(dict: Dict[T, U], key: T) -> U:
    """For key key, returns value"""
    pass


def pop(dict: Dict[T, U], key: T) -> U:
    """Removes the key key in the dictionary dict and returns its value."""
    pass


def popitem(dict: Dict[T, U]) -> Tuple[T, U]:
    """Removes and returns an arbitrary (key, value) pair from the dictionary dict."""
    pass


def update(dict: Dict[T, U], dict2: Dict[T, U]) -> None:
    """Adds dictionary dict2's key-values pairs to dict"""
    pass

def items(dict: Dict[T, U]) -> List[Tuple[T, U]]:
    pass
