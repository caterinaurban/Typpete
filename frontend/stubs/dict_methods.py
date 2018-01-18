"""Stub file for methods invoked on lists"""
from typing import TypeVar, Dict, List, Tuple, Generic

T = TypeVar("T")
U = TypeVar("U")


def clear(self: Dict[T, U]) -> None:
    """Removes all elements of dictionary dict"""
    pass


def copy(self: Dict[T, U]) -> Dict[T, U]:
    """Returns a shallow copy of dictionary dict"""
    pass


def get(self: Dict[T, U], key: T, default: U = None) -> U:
    """For key key, returns value"""
    pass

def __getitem__(self: Dict[T, U], item: T) -> U:
    pass

def __setitem__(self: Dict[T, U], key: T, value: U) -> None:
    pass


def pop(self: Dict[T, U], key: T) -> U:
    """Removes the key key in the dictionary dict and returns its value."""
    pass


def popitem(self: Dict[T, U]) -> Tuple[T, U]:
    """Removes and returns an arbitrary (key, value) pair from the dictionary dict."""
    pass


def update(self: Dict[T, U], dict2: Dict[T, U]) -> None:
    """Adds dictionary dict2's key-values pairs to dict"""
    pass

def items(self: Dict[T, U]) -> List[Tuple[T, U]]:
    pass
