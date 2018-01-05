"""Stub file for methods invoked on lists"""
from typing import TypeVar, Dict, List, Tuple, Generic

T = TypeVar("T")
U = TypeVar("U")

class Dict(Generic[T, U]):
    def clear(self) -> None:
        """Removes all elements of dictionary dict"""
        pass
    
    
    def copy(self) -> Dict[T, U]:
        """Returns a shallow copy of dictionary dict"""
        pass
    
    
    def get(self, key: T) -> U:
        """For key key, returns value"""
        pass

    def __getitem__(self, item: T) -> U:
        pass

    def __setitem__(self, key: T, value: U) -> None:
        pass
    
    
    def pop(self, key: T) -> U:
        """Removes the key key in the dictionary dict and returns its value."""
        pass
    
    
    def popitem(self) -> Tuple[T, U]:
        """Removes and returns an arbitrary (key, value) pair from the dictionary dict."""
        pass
    
    
    def update(self, dict2: Dict[T, U]) -> None:
        """Adds dictionary dict2's key-values pairs to dict"""
        pass
    
    def items(self) -> List[Tuple[T, U]]:
        pass
