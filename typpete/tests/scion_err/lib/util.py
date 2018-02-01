from typing import Dict, Optional

class SCIONTime(object):
    #_custom_time = None  # type: None

    @staticmethod
    def get_time() -> int: ...

    @staticmethod
    def set_time_method(method:Optional[object]=None) -> None: ...

def load_yaml_file(file_path: str) -> Dict[str, object]:
    ...



class Raw:
    def __init__(self, data: bytes, desc:str="", len_:int=None,
                 min_:bool=False) -> None:  # pragma: no cover
        self._data = data
        self._desc = desc
        self._len = len_
        self._min = min_
        self._offset = 0

    def pop(self, n: int = None) -> bytes:
        ...

    def __len__(self) -> int:
        ...




def sleep_interval(start: float, interval: float, desc: str, quiet: bool =False) -> None:
    ...


def hex_str(raw: bytes) -> str:
    ...

def calc_padding(length: int, block_size: int) -> int:
    if length % block_size:
        return block_size - (length % block_size)
    else:
        return 0