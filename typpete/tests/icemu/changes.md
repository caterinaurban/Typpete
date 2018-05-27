### chip.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Declared Chip class as abstract | 4 | Logically, it is an abstract class, and its subclass Gate has abstract method. |
| Replaced kwargs by normal args | 11, 14, 16 | kwargs are not supported |
| Replaced generator expression by list comprehension | 20, 21, 63 | Generator expressions are not supported |
| Added `Pin` return annotation to getpin method | 59 | `getattr` returns static type `object` |

### counters.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Commented `super()` call | 10 | `super` calls are not supported |

### gates.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Added `@abstractmethod` decorator to _test | 9 | To allow it to have non-`None` type. It is intended to be abstract by raising `NotImplementedError`. |
| Replaced generator expression by list comprehension | 20, 24, 28, 32 | Generator expressions are not supported |
| Replace starred variables by normal variables | 12, 44, 52, 61, 71, 80, 109 | Starred variables are not supported |
| Replace some tuples by lists | 12, 44, 52, 61, 71, 80, 109 | Tuple slicing produces a general tuple type |

### pin.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Replaced generator expression by list comprehension | 15, 16 | Generator expressions are not supported |

### seg7.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Replaced vararg by normal arg | 22 | varargs are not supported |
| Replaced generator expression by list comprehension | 26:28, 49 | Generator expressions are not supported |
| Commented `super()` call | 35 | `super` calls are not supported |
| Replaced comprehension by a loop | 49 | Having tuple as iteration target in comprehension is not supported |

### shiftregisters.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Commented `super()` call | 15 | `super` calls are not supported |
| Replaced kwargs by normal args | 25 | kwars are not supported |
| Replaced generator expression by list comprehension | 35 | Generator expressions are not supported |

