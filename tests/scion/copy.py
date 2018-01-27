from typing import TypeVar

Tcopy = TypeVar('Tcopy', bound=object)
def deepcopy(o: Tcopy) -> Tcopy:
    ...