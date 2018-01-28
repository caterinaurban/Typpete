from typing import TypeVar, List, Union, Dict

T = TypeVar('T')

class Dialect(object):
    delimiter = ""  # type: str
    quotechar = ""  # type: Optional[str]
    escapechar = ""  # type: Optional[str]
    doublequote = True  # type: bool
    skipinitialspace = True  # type: bool
    lineterminator = ""  # type: str
    quoting = 0  # type: int
    def __init__(self) -> None: ...

class excel(Dialect):
    pass

class excel_tab(excel):
    pass

class unix_dialect(Dialect):
    pass

# Uncomment after supporting generics
# class DictWriter(object):
#     fieldnames = [''] # type: Sequence[str]
#     extrasaction = ''
#
#     def __init__(self, f: Any, fieldnames: List[str],
#                  restval: Any = ..., extrasaction: str = ...,
#                  dialect: Union[str, Dialect] = ...) -> None: ...
#     def writeheader(self) -> None: ...
#     def writerow(self, rowdict: Dict[str, Any]) -> None: ...
#     def writerows(self, rowdicts: List[Dict[str, Any]]) -> None: ...

class Sniffer(object):
    preferred = ...  # type: List[str]
    def __init__(self) -> None: ...
    def sniff(self, sample: str, delimiters: str = ...) -> Dialect: ...
    def has_header(self, sample: str) -> bool: ...