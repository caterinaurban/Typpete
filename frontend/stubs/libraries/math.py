from typing import Tuple, List

e = 2.718281828459045

pi = 3.141592653589793


# functions
def acos(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    acos(x)

    Return the arc cosine (measured in radians) of x.
    """
    pass


def acosh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    acosh(x)

    Return the inverse hyperbolic cosine of x.
    """
    pass


def asin(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    asin(x)

    Return the arc sine (measured in radians) of x.
    """
    pass


def asinh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    asinh(x)

    Return the inverse hyperbolic sine of x.
    """
    pass


def atan(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    atan(x)

    Return the arc tangent (measured in radians) of x.
    """
    pass


def atan2(y: float, x: float) -> float:  # real signature unknown; restored from __doc__
    """
    atan2(y, x)

    Return the arc tangent (measured in radians) of y/x.
    Unlike atan(y/x), the signs of both x and y are considered.
    """
    pass


def atanh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    atanh(x)

    Return the inverse hyperbolic tangent of x.
    """
    pass


def ceil(x: float) -> int:  # real signature unknown; restored from __doc__
    """
    ceil(x)

    Return the ceiling of x as an Integral.
    This is the smallest integer >= x.
    """
    pass


def copysign(x: float, y: float) -> float:  # real signature unknown; restored from __doc__
    """
    copysign(x, y)

    Return a float with the magnitude (absolute value) of x but the sign 
    of y. On platforms that support signed zeros, copysign(1.0, -0.0) 
    returns -1.0.
    """
    pass


def cos(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    cos(x)

    Return the cosine of x (measured in radians).
    """
    pass


def cosh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    cosh(x)

    Return the hyperbolic cosine of x.
    """
    pass


def degrees(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    degrees(x)

    Convert angle x from radians to degrees.
    """
    pass


def erf(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    erf(x)

    Error function at x.
    """
    pass


def erfc(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    erfc(x)

    Complementary error function at x.
    """
    pass


def exp(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    exp(x)

    Return e raised to the power of x.
    """
    pass


def expm1(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    expm1(x)

    Return exp(x)-1.
    This function avoids the loss of precision involved in the direct evaluation of exp(x)-1 for small x.
    """
    pass


def fabs(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    fabs(x)

    Return the absolute value of the float x.
    """
    pass


def factorial(x: int) -> int:  # real signature unknown; restored from __doc__
    """
    factorial(x) -> Integral

    Find x!. Raise a ValueError if x is negative or non-integral.
    """
    pass


def floor(x: float) -> int:  # real signature unknown; restored from __doc__
    """
    floor(x)

    Return the floor of x as an Integral.
    This is the largest integer <= x.
    """
    pass


def fmod(x: float, y: float) -> float:  # real signature unknown; restored from __doc__
    """
    fmod(x, y)

    Return fmod(x, y), according to platform C.  x % y may differ.
    """
    pass


def frexp(x: float) -> Tuple[float, int]:  # real signature unknown; restored from __doc__
    """
    frexp(x)

    Return the mantissa and exponent of x, as pair (m, e).
    m is a float and e is an int, such that x = m * 2.**e.
    If x is 0, m and e are both 0.  Else 0.5 <= abs(m) < 1.0.
    """
    pass


def fsum(iterable: List[float]) -> float:  # real signature unknown; restored from __doc__
    """
    fsum(iterable)
    
    Return an accurate floating point sum of values in the iterable.
    Assumes IEEE-754 floating point arithmetic.
    
    TODO: Add support for all iterables after implementing interfaces
    """
    pass


def gamma(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    gamma(x)

    Gamma function at x.
    """
    pass


def gcd(x: int, y: int) -> int:  # real signature unknown; restored from __doc__
    """
    gcd(x, y) -> int
    greatest common divisor of x and y
    """
    return 0


def hypot(x: float, y: float) -> float:  # real signature unknown; restored from __doc__
    """
    hypot(x, y)

    Return the Euclidean distance, sqrt(x*x + y*y).
    """
    pass


def isclose(a: float, b: float) -> bool:  # real signature unknown; NOTE: unreliably restored from __doc__
    """
    isclose(a, b, *, rel_tol=1e-09, abs_tol=0.0) -> bool

    Determine whether two floating point numbers are close in value.

       rel_tol
           maximum difference for being considered "close", relative to the
           magnitude of the input values
        abs_tol
           maximum difference for being considered "close", regardless of the
           magnitude of the input values

    Return True if a is close in value to b, and False otherwise.

    For the values to be considered close, the difference between them
    must be smaller than at least one of the tolerances.

    -inf, inf and NaN behave similarly to the IEEE 754 Standard.  That
    is, NaN is not close to anything, even itself.  inf and -inf are
    only close to themselves.
    """
    pass


def isfinite(x: float) -> bool:  # real signature unknown; restored from __doc__
    """
    isfinite(x) -> bool

    Return True if x is neither an infinity nor a NaN, and False otherwise.
    """
    return False


def isinf(x: float) -> bool:  # real signature unknown; restored from __doc__
    """
    isinf(x) -> bool

    Return True if x is a positive or negative infinity, and False otherwise.
    """
    return False


def isnan(x: float) -> bool:  # real signature unknown; restored from __doc__
    """
    isnan(x) -> bool

    Return True if x is a NaN (not a number), and False otherwise.
    """
    return False


def ldexp(x: float, i: int) -> float:  # real signature unknown; restored from __doc__
    """
    ldexp(x, i)

    Return x * (2**i).
    """
    pass


def lgamma(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    lgamma(x)

    Natural logarithm of absolute value of Gamma function at x.
    """
    pass


def log(x: float, base: float) -> float:  # real signature unknown; restored from __doc__
    """
    log(x[, base])
    TODO make base optional
    Return the logarithm of x to the given base.
    If the base not specified, returns the natural logarithm (base e) of x.
    """
    pass


def log10(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    log10(x)

    Return the base 10 logarithm of x.
    """
    pass


def log1p(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    log1p(x)

    Return the natural logarithm of 1+x (base e).
    The result is computed in a way which is accurate for x near zero.
    """
    pass


def log2(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    log2(x)

    Return the base 2 logarithm of x.
    """
    pass


def modf(x: float) -> Tuple[float, float]:  # real signature unknown; restored from __doc__
    """
    modf(x)

    Return the fractional and integer parts of x.  Both results carry the sign
    of x and are floats.
    """
    pass


def pow(x: float, y: float) -> float:  # real signature unknown; restored from __doc__
    """
    pow(x, y)

    Return x**y (x to the power of y).
    """
    pass


def radians(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    radians(x)

    Convert angle x from degrees to radians.
    """
    pass


def sin(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    sin(x)

    Return the sine of x (measured in radians).
    """
    pass


def sinh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    sinh(x)

    Return the hyperbolic sine of x.
    """
    pass


def sqrt(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    sqrt(x)

    Return the square root of x.
    """
    pass


def tan(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    tan(x)

    Return the tangent of x (measured in radians).
    """
    pass


def tanh(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    tanh(x)

    Return the hyperbolic tangent of x.
    """
    pass


def trunc(x: float) -> float:  # real signature unknown; restored from __doc__
    """
    trunc(x:Real) -> Integral

    Truncates x to the nearest Integral toward 0. Uses the __trunc__ magic method.
    """
    pass
