from typing import Callable, Type, TypeVar

_FuncT = TypeVar('_FuncT', bound=Callable[[], object])

class ABCMeta:
    pass

def abstractmethod(callable: _FuncT) -> _FuncT: ...
def abstractproperty(callable: _FuncT) -> _FuncT: ...
# These two are deprecated and not supported by mypy
def abstractstaticmethod(callable: _FuncT) -> _FuncT: ...
def abstractclassmethod(callable: _FuncT) -> _FuncT: ...


class ABC(metaclass=ABCMeta):
    pass

def get_cache_token() -> object: ...