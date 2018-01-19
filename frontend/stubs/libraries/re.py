from typing import Dict, List, Union, TypeVar, Tuple, Callable

# ----- re variables and constants -----
DEBUG = 0
I = 0
IGNORECASE = 0
L = 0
LOCALE = 0
M = 0
MULTILINE = 0
S = 0
DOTALL = 0
X = 0
VERBOSE = 0
U = 0
UNICODE = 0
T = 0
TEMPLATE = 0

Any = TypeVar('Any')

class Match:
    pos = 0
    endpos = 0
    lastindex = 0
    lastgroup = ""
    string = ""

    # The regular expression object whose match() or search() method produced
    # this match instance.
    re = Pattern()

    def expand(self, template: str) -> str: ...

    def group(self, group1: int = 1) -> str: ...

    def groups(self, default: str = "") -> List[str]: ...

    def groupdict(self, default: str = "") -> Dict[str, str]: ...

    def end(self, group: int = 1) -> int: ...

class Pattern:
    flags = 0
    groupindex = 0
    groups = 0
    pattern = ""

    def match(self, string: str, pos: int = 1, endpos: int = 1) -> Match: ...

def compile(pattern: Union[Pattern, str], flags: int = 1) -> Pattern: ...

def search(pattern: Union[Pattern, str], string: str, flags: int = 1) -> Match: ...

def match(pattern: Union[Pattern, str], string: str, flags: int = 1) -> Match: ...

def fullmatch(pattern: Union[Pattern, str], string: str, flags: int = 1) -> Match: ...

def split(pattern: Union[Pattern, str], maxsplit: int = 1, flags: int = 1) -> Match: ...

def findall(pattern: Union[Pattern, str], maxsplit: int = 1, flags: int = 1) -> List[Any]: ...

def sub(pattern: Union[Pattern, str], repl: Union[str, Callable[[Match], str]],
        string: str, count: int = 0, flags: int = 0) -> str: ...

def subn(pattern: Union[Pattern, str], repl: Union[str, Callable[[Match], str]],
         string: str, count: int = 0, flags: int = 0) -> Tuple[str, int]: ...


def escape(string: str) -> str: ...

def template(pattern: Union[str, Pattern], flags: int = 1) -> Pattern: ...
