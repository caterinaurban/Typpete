#### lib/path_store.py:

| Change | Line # | Justification |
|--------|--------|---------------|
| Moved nested function out of method _check_property_ranges | 101ff | Nested functions not supported by inference. |
| Adapted calls to formerly nested functions | 120ff | See above |
| Turned classmethod into staticmethod | 146 | Classmethods currently not supported by inference. |
| Turned classmethod into staticmethod | 155 | Classmethods currently not supported by inference. |
| Added type casts | 172ff | Code expects dict values to have different types for different keys, not statically typable otherwise. |
| Added local variable | 183 | Local variable reassigned with different type, not statically typable | 
| Added attribute to constructor | 239 | Inference requires constructors to define all attributes | 
| Changed keyword arg to normal arg | 308 | Keyword arg passing not supported | 
| Changed float into lambda x: float() | 309 | Special handling for built-in functions prevents passing them around as values | 
| Changed keyword arg to normal arg | 453 | Keyword arg passing not supported |


#### lib/packet/scion_addr.py:

| Change | Line # | Justification |
|--------|--------|---------------|
| Turned classmethod into staticmethod | 87 | Classmethods currently not supported by inference. |
| Changed call target from self to class | 103 | Staticmethod calls only supported directly on classes | 
| Turned generator into function returning list | 127 | Generators not supported |
| Turned classmethod into staticmethod | 175 | Classmethods currently not supported by inference. |
| Turned classmethod into staticmethod | 176 | Classmethods currently not supported by inference. |
