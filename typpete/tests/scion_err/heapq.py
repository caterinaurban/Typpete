from typing import List, TypeVar, Callable

T = TypeVar("T")

def nlargest(n: int, iterable: List[T], key: Callable[[T], float]) -> List[T]:
    ...