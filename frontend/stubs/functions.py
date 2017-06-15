"""Stub file for built in functions"""


def abs(x: number):
    """Return the absolute value of the argument. """
    return x


def all(x: sequence) -> bool:
    """
    Return True if bool(x) is True for all values x in the iterable.

    If the iterable is empty, return True.
    """
    pass


def any(_: sequence) -> bool:
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


def bool(_: object) -> bool:
    """Convert a value to a Boolean."""
    pass


def bytes(_: bytes) -> bytes:
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


def complex() -> complex:
    """Create a complex number"""
    pass


def dict():
    """Create a new dictionary."""
    return {}


def dir() -> List[str]:
    """Return the list of names in the current local scope."""
    pass


def divmod(x: float, y: float) -> Tuple[int, int]:
    """ Return the tuple (x//y, x%y).  Invariant: div*y + mod == x. """
    pass


def float(x: Union[str, number]) -> float:
    """Convert a string or a number to floating point."""
    pass


def format(x: object) -> str:
    """Convert a value to a "formatted" representation."""
    pass


def hash(x: object) -> int:
    """
    Return the hash value for the given object.
    
    Two objects that compare equal must also have the same hash value, but the
    reverse is not necessarily true."""
    pass


def id(x: object) -> int:
    """
    Return the identity of an object.

    This is guaranteed to be unique among simultaneously existing objects.
    (CPython uses the object's memory address.)
    """
    pass


def input() -> str:
    """
    Read a string from standard input.  The trailing newline is stripped.

    The prompt string, if given, is printed to standard output without a
    trailing newline before reading input.

    If the user hits EOF (*nix: Ctrl-D, Windows: Ctrl-Z+Return), raise EOFError.
    On *nix systems, readline is used if available.
    """
    pass


def int(x: Union[number, str]) -> int:
    """Convert a number or string to an integer."""
    pass


def len(x: sequence) -> int:
    """ Return the number of items in a container. """
    pass


def object() -> object:
    """Return a new featureless object."""
    pass


def oct(x: int) -> str:
    """
    Return the octal representation of an integer.

       >>> oct(342391)
       '0o1234567'
    """
    pass


def pow(x, y):
    """Equivalent to x**y"""
    return x ** y


def repr(x: object) -> str:
    """
    Return the canonical string representation of the object.

    For many object types, including most builtins, eval(repr(obj)) == obj.
    """
    pass


def round(x: float) -> int:
    """
    round(number[, ndigits]) -> number

    Round a number to a given precision in decimal digits (default 0 digits).
    This returns an int when called with one argument, otherwise the
    same type as the number. ndigits may be negative.
    """
    pass


def str(x: object) -> str:
    """Return a str version of object."""
    pass
