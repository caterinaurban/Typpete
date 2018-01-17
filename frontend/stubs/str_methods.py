"""Stub file for methods invoked on strings

TODO make some arguments optional
"""
from typing import List


def capitalize(s: str) -> str:
    """Return a new string with the first letter capitalized"""
    pass


def center(s: str, width: int, fillchar: str) -> str:
    """Returns a space-padded string with the original string centered to a total of width columns."""
    pass


def count(s: str, str: str) -> int:
    """Counts how many times str occurs in string"""
    pass

def format(self, arg1: object = '', arg2: object = '', arg3: object = '') -> str:
    """
    Return a formatted version of S, using substitutions from args and kwargs.
        The substitutions are identified by braces ('{' and '}').
    """
    pass


def isalnum(s: str) -> bool:
    """Returns true if string has at least 1 character and all characters are alphanumeric and false otherwise."""
    pass


def isalpha(s: str) -> bool:
    """Returns true if string has at least 1 character and all characters are alphabetic and false otherwise."""
    pass


def isdecimal(s: str) -> bool:
    """Returns true if a unicode string contains only decimal characters and false otherwise."""
    pass


def isdigit(s: str) -> bool:
    """Returns true if string contains only digits and false otherwise."""
    pass


def islower(s: str) -> bool:
    """Returns true if string has at least 1 character and all cased characters are in lowercase and false otherwise."""
    pass


def isnumeric(s: str) -> bool:
    """Returns true if a unicode string contains only numeric characters and false otherwise."""
    pass


def isspace(s: str) -> bool:
    """Returns true if string contains only whitespace characters and false otherwise."""
    pass


def istitle(s: str) -> bool:
    """Returns true if string is properly "titlecased" and false otherwise."""
    pass


def isupper(s: str) -> bool:
    """Returns true if string has at least one character and all characters are in uppercase and false otherwise."""
    pass


def join(s: str, seq: List[str]) -> str:
    """Concatenates the string representations of elements in sequence seq into a string, with separator string."""
    pass


def lower(s: str) -> str:
    """Converts all uppercase letters in string to lowercase."""
    pass


def lstrip(s: str) -> str:
    """Removes all leading whitespace in string."""
    pass


def replace(s: str, old: str, new: str) -> str:
    """Replaces all occurrences of old in string with new"""
    pass


def rstrip(s: str) -> str:
    """Removes all trailing whitespace of string."""
    pass


def split(s: str, delimiter: str) -> List[str]:
    """Splits string according to delimiter str and returns list of substrings"""
    pass

def startswith(self, c: str) -> bool:
    """"""
    pass


def strip(s: str) -> str:
    """Performs both lstrip() and rstrip() on string"""
    pass


def swapcase(s: str) -> str:
    """Inverts case for all letters in string."""
    pass


def title(s: str) -> str:
    """Returns "titlecased" version of string, that is, all words begin with uppercase and the rest are lowercase."""
    pass


def upper(s: str) -> str:
    """Converts lowercase letters in string to uppercase."""
    pass
