#### combinators.py:

| Change | Line # | Justification |
|--------|--------|---------------|
| Added `__call__` method to Parser class | 49 | Implemented by every subclass |
| Downcast `arg` to None | 154 | `self.function` expects a subtype of None as an arg |

#### equality.py:

| Change | Line # | Justification |
|--------|--------|---------------|
| added `eval` method to Equality class | 34 | Implemented by every subclass |

#### imp_ast.py:
| Change | Line # | Justification |
|--------|--------|---------------|
| added `value` variable before branching | 127,152 | Not declared in else branch and used after branch |

#### imp_parser.py:
| Change | Line # | Justification |
|--------|--------|---------------|
| Renamed `id` to `id2` | 37 | Shadows builtin function `id` |
| Moved `*_precedence_levels` variables to top | 30 | Global variables must be encounterd before functions they are used in |
| Replaced `reduce` Python 2 function with a Python 3 implementation | 188 | The type inference currently supports Python 3 only |

#### imp.py:
| Change | Line # | Justification |
|--------|--------|---------------|
| Set `text` to empty string | 42 | File handling is not supported yet |
| Downcast `ast` to `Equality` | 48 | parse_result.value has static type `object`, but a subtype of `Equality` at runtime |