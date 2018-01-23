from typing import Generic, TypeVar, Dict, Type, List, Callable


T = TypeVar('T')
V = TypeVar('V')

def defaultdict(factory: Callable[[], V]) -> Dict[T, V]:
    ...

def deque(maxlen: int = 0) -> List[T]:
    ...