"""Stub file for built in functions"""
from typing import TypeVar, List, Tuple, Dict, Set, Union, Type, Callable, Generic
from sys import IO

Tf = TypeVar("Tf")
Uf = TypeVar("Uf")
Num = TypeVar("Num", bound=complex)
IntOrFloat = TypeVar("IntOrFloat", int, float)
Str = TypeVar("Str", str, bytes)
Seq = TypeVar("Seq", Str, List[Tf])
NumOrStr = TypeVar("NumOrStr", Num, Str)
NumOrStrNoComplex = TypeVar("NumOrStr", bool, int, float, Str)


class Exception():
    pass

Titer = TypeVar("Titer")
class Iterator(Generic[Titer]):
    pass


def abs(x: Num) -> Num:
    """Return the absolute value of the argument. """
    pass


def all(_: Seq) -> bool:
    """
    Return True if bool(x) is True for all values x in the iterable.

    If the iterable is empty, return True.
    """
    pass


def any(_: Seq) -> bool:
    """
    Return True if bool(x) is True for any x in the iterable.

    If the iterable is empty, return False.
    """
    pass


def ascii(_: object) -> str:
    """
    Return an ASCII-only representation of an object.

    As repr(), return a string containing a printable representation of an
    object, but escape the non-ASCII characters in the string returned by
    repr() using \\x, \\u or \\U escapes. This generates a string similar
    to that returned by repr() in Python 2.
    """
    pass


def bin(_: int) -> str:
    """
    Return the binary representation of an integer.

       >>> bin(2796202)
       '0b1010101010101010101010'
    """
    pass


def bool(_: object = None) -> bool:
    """Convert a value to a Boolean."""
    pass


def bytes(_: object = None) -> bytes:
    """Return a new "bytes" object."""
    pass


def callable(_: object) -> bool:
    """
    Return whether the object is callable (i.e., some kind of function).

    Note that classes are callable, as are instances of classes with a
    __call__() method.
    """
    pass


def chr(_: int) -> str:
    """ Return a Unicode string of one character with ordinal i; 0 <= i <= 0x10ffff. """
    pass


def complex(_: NumOrStr = None) -> complex:
    """Create a complex number"""
    pass


def dict(_: Dict[Tf, Uf] = None) -> Dict[Tf, Uf]:
    """Create a new dictionary.
    Make argument of type Mappable after implementing interfaces
    """
    pass


def dir(_: object = None) -> List[str]:
    """Return the list of names in the current local scope."""
    pass


def divmod(_: IntOrFloat, __: IntOrFloat) -> Tuple[IntOrFloat, IntOrFloat]:
    """ Return the tuple (x//y, x%y).  Invariant: div*y + mod == x. """
    pass

def enumerate(l: List[Tf]) -> List[Tuple[int, Tf]]:
    """Iterate over a list with key and value"""
    pass


def float(_: NumOrStrNoComplex = None) -> float:
    """Convert a string or a number to floating point."""
    pass


def format(_: object) -> str:
    """Convert a value to a "formatted" representation."""
    pass


def getattr(o: object, name: str) -> object:
    """
    Return the value of the named attribute of object.
    Name must be a string. If the string is the name of one of the object’s attributes,
    the result is the value of that attribute.
    For example, getattr(x, 'foobar') is equivalent to x.foobar.
    """
    pass


def hasattr(o: object, attr: str) -> bool:
    """Check if an object has an attribute"""
    pass


def hash(_: object) -> int:
    """
    Return the hash value for the given object.

    Two objects that compare equal must also have the same hash value, but the
    reverse is not necessarily true."""
    pass


def hex(_: int) -> str:
    """
    Return the hexadecimal representation of an integer.

       >>> hex(12648430)
       '0xc0ffee'
    """
    pass


def id(_: object) -> int:
    """
    Return the identity of an object.

    This is guaranteed to be unique among simultaneously existing objects.
    (CPython uses the object's memory address.)
    """
    pass


def input(_: object = None) -> str:
    """
    Read a string from standard input.  The trailing newline is stripped.

    The prompt string, if given, is printed to standard output without a
    trailing newline before reading input.

    If the user hits EOF (*nix: Ctrl-D, Windows: Ctrl-Z+Return), raise EOFError.
    On *nix systems, readline is used if available.
    """
    pass


def int(_: NumOrStrNoComplex = None, base: int = 10) -> int:
    """Convert a number or string to an integer."""
    pass


def isinstance(x: object, y: object) -> bool:
    """Check if object x is an instance of type y"""
    pass



def iter(l: List[Tf]) -> Iterator[Tf]:
    pass


def next(l: Iterator[Tf]) -> Tf:
    pass


def len(_: object) -> int:
    """ Return the number of items in a container. """
    pass


def list(_: Union[List[Tf], Set[Tf], Dict[Tf, Uf], Iterator[Tf]]) -> List[Tf]:
    pass


def min(_: List[Tf]) -> Tf:
    """Return the minimum object from the list

    TODO:
        - Verify that the argument is comparable
        - Add support for different iterable objects
    """
    pass


def max(_: List[Tf]) -> Tf:
    """Return the maximum object from the list any

    TODO:
        - Verify that the argument is comparable
        - Add support for different iterable objects
    """
    pass


def object() -> object:
    """Return a new featureless object."""
    pass


def oct(_: int) -> str:
    """
    Return the octal representation of an integer.

       >>> oct(342391)
       '0o1234567'
    """
    pass


def open(file: Union[str, bytes, int], mode: str = None,
         buffering: int = None, encoding: str = None, errors: str = None, newline: str = None, closefd: bool = None) -> IO:
    """Open a file stream"""
    pass


def pow(x, y):
    """Equivalent to x**y"""
    return x ** y


def print(_: object) -> None:
    """Print an object"""
    pass


def range(x: int, y:int=None, z:int=None) -> List[int]:
    """Return a list of int from 0 (inclusive) to `x` (exclusive)

    TODO: make it RangeObject after implementing interfaces
    """
    pass


def repr(_: object) -> str:
    """
    Return the canonical string representation of the object.

    For many object types, including most builtins, eval(repr(obj)) == obj.
    """
    pass


def reversed(_: List[Tf]) -> Iterator[Tf]:
    """Return a reversed version of the input list

    TODO: make it return reversed object after implementing interfaces
    """
    pass


def round(_: float) -> int:
    """
    round(number[, ndigits]) -> number

    Round a number to a given precision in decimal digits (default 0 digits).
    This returns an int when called with one argument, otherwise the
    same type as the number. ndigits may be negative.
    """
    pass


def set(l: List[Tf] = None) -> Set[Tf]:
    """Create a set of unique elements

    If the parameter is provided, use the elements in the list to create the set,
    otherwise, create an empty set."""
    pass


def setattr(o: object, name: str, val: object) -> None:
    """Assign `val` to the attribute, provided the object allows it.
    For example, setattr(x, 'foobar', 123) is equivalent to x.foobar = 123.
    """
    pass


def sorted(_: List[Tf], key: Callable[[Tf], float]=lambda x: 1.0, reverse: bool=None) -> List[Tf]:
    """Return the input list in a sorted order

    TODO: Add support for different iterable objects
    """
    pass


def str(_: object = None) -> str:
    """Return a str version of object."""
    pass


def sum(_: List[Num]) -> Num:
    """Return the sum of numbers in a list

    TODO: Add support for different iterable objects
    """
    pass


def type(o: Tf) -> Type[Tf]:
    pass


def zip(x: Union[List[Tf], str], y: List[Uf]) -> List[Tuple[Tf, Uf]]:
    """This function returns a list of tuples,
    where the i-th tuple contains the i-th element from each of the argument lists"""
    pass