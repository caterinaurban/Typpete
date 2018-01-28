"""Stub file for methods invoked on lists"""
from typing import TypeVar, Dict, List, Tuple, Generic

Tdict = TypeVar("Tdict")
Udict = TypeVar("Udict")


def clear(self: Dict[Tdict, Udict]) -> None:
    """Removes all elements of dictionary dict"""
    pass


def copy(self: Dict[Tdict, Udict]) -> Dict[Tdict, Udict]:
    """Returns a shallow copy of dictionary dict"""
    pass


def get(self: Dict[Tdict, Udict], key: Tdict, default: Udict = None) -> Udict:
    """For key key, returns value"""
    pass

def __getitem__(self: Dict[Tdict, Udict], item: Tdict) -> Udict:
    pass

def __setitem__(self: Dict[Tdict, Udict], key: Tdict, value: Udict) -> None:
    pass


def pop(self: Dict[Tdict, Udict], key: Tdict) -> Udict:
    """Removes the key key in the dictionary dict and returns its value."""
    pass


def popitem(self: Dict[Tdict, Udict]) -> Tuple[Tdict, Udict]:
    """Removes and returns an arbitrary (key, value) pair from the dictionary dict."""
    pass


def update(self: Dict[Tdict, Udict], dict2: Dict[Tdict, Udict]) -> None:
    """Adds dictionary dict2's key-values pairs to dict"""
    pass

def items(self: Dict[Tdict, Udict]) -> List[Tuple[Tdict, Udict]]:
    pass


def keys(dict: Dict[Tdict, Udict]) -> List[Tdict]:
    pass


def values(dict: Dict[Tdict, Udict]) -> List[Udict]:
    pass