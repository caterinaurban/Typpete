from typing import TypeVar, List

T = TypeVar("T")

def chain(a: List[List[T]]) -> List[T]:
    """Return elements from the first iterable until it is exhausted,
    then elements from the next iterable, until all of the iterables are exhausted"""
    pass