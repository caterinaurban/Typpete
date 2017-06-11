from math import inf
from typing import Tuple


class CDBM():
    """Coherent Difference Bound Matrix
    
    A DBM-matrix `m` is *coherent* if matrix entries that represent the same condition do agree on the bound. 
    
    .. image:: _static/coherence.png
    
    **NOTE:** we use 0-based indices instead.
    
    This implies that the matrix as a special kind of symmetric. It is enough to store the lower left diagonal matrix 
    (s plus A), the diagonal (D) **plus** parts of one more adjacent diagonal `B` to the right, which contains unary 
    conditions that may be different from the already included diagonal `A`. 
     
    ::
    
        D B
        A D
        s A D B
        s s A D
        s s s A D B
        s s s s A D
    
    
    """

    def __init__(self, size):
        assert size % 2 == 0, "The size of a CDBM has to be even!"

        self._size = size
        self._m = []
        for i in range(size):
            row = [inf] * min((i + 2) // 2 * 2, size)
            self._m.append(row)

    @property
    def size(self):
        return self._size

    def __getitem__(self, index_tuple: Tuple[int, int]):
        row, col = self._correct_index(index_tuple)
        return self._m[row][col]

    def __setitem__(self, index_tuple: Tuple[int, int], value):
        row, col = self._correct_index(index_tuple)
        self._m[row][col] = value

    @staticmethod
    def _correct_index(index_tuple: Tuple[int, int]):
        """Corrects the given index to index into represented part of DBM"""
        row, col = index_tuple
        if row + 1 < col:
            return col ^ 1, row ^ 1
        else:
            return row, col

    def keys(self):
        row = 0
        col = 0
        while row < self.size:
            current_index = row, col  # make a copy (as a index tuple)

            col += 1
            if row // 2 * 2 + 1 < col:
                # wrap line
                col = 0
                row += 1

            yield current_index

    def values(self):
        for key in self.keys():
            yield self[key]

    def items(self):
        for key in self.keys():
            yield key, self[key]

    def __str__(self):
        return "\n".join([" \t".join(map(lambda x: str(x).rjust(5), self._m[row])) for row in range(self._size)])
