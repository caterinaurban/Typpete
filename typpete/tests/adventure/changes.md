### model.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Added HasN superclass | 7 | For inferring generic type argument in `data.py` file. |
| Add `n` attribute to some classes | 65, 98, 125, 173 | It is dynamically added |
| Replaced generator expression by list comprehension | 104, 134 | Generator expressions are not supported |
| Inverted `not isinstance(...) ... else ...` to `isisntance(...) ... else ...` | 59 | `isinstance` test inference only supports this normal form |

### data.py
| Change | Line # | Justification |
|--------|--------|---------------|
| Added some attributes to `Data` class | 34 | They are dynamically added. |
| Replaced vararg by normal arg | 61, 64, 112, 134, 147, 152, 191 | varargs are not supported |
| Extended tuples in different branches to be same length | 81 | Subtyping relatonships exists between only tuples of same length |
| Replaced `Type` types passed to `make_object` with `lambda` functions | ... | Required for generic typevars inference. |