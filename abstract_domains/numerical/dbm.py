from abc import ABCMeta, abstractmethod
from math import inf, isinf, isnan
from typing import Tuple


def nan2inf(f):
    return inf if isnan(f) else f


class CDBM(metaclass=ABCMeta):
    """Coherent Difference Bound Matrix.
    
    A DBM-matrix `m` is *coherent* if matrix entries that represent the same condition do agree on the bound. 
    
    .. image:: _static/coherence.png
    
    **NOTE:** we use 0-based indices instead.
    
    This implies that the matrix as a special kind of symmetric. It is enough to store the lower left diagonal matrix 
    (``s`` plus ``A``), the diagonal (``D``) **plus** parts of one more adjacent diagonal ``B`` to the right, 
    which contains unary conditions that may be different from the already included diagonal ``A``. 
     
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

    @property
    def strongly_closed(self):
        triang_eq = all([self[i, j] <= self[i, k] + self[k, j]
                         for i in range(self.size) for j in range(self.size) for k in range(self.size)])
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    if not self[i, j] <= self[i, k] + self[k, j]:
                        print(f"{self[i, j]} !<= {self[i, k]} + {self[k, j]} \t ({i},{j}) !<= ({i},{k}) + ({k},{j})")
        cond = all([self[i, j] <= nan2inf((self[i, i ^ 1] + self[j ^ 1, j]) // 2)
                    for i in range(self.size) for j in range(self.size)])
        diag_zero = all([self[i, i] == 0 for i in range(self.size)])
        # print(f"triang_eq={triang_eq}, cond={cond}, diag_zero={diag_zero}")
        return triang_eq and cond and diag_zero

    @property
    def tightly_closed(self):
        unary_cond_tight = all([isinf(self[i, i ^ 1]) or self[i, i ^ 1] % 2 == 0 for i in range(self.size)])
        # print(f"unary_cond_tight={unary_cond_tight}")
        return self.strongly_closed and unary_cond_tight

    def __getitem__(self, index_tuple: Tuple[int, int]):
        row, col = self._map_index(index_tuple)
        return self._m[row][col]

    def __setitem__(self, index_tuple: Tuple[int, int], value):
        row, col = self._map_index(index_tuple)
        self._m[row][col] = value

    @staticmethod
    def _map_index(index_tuple: Tuple[int, int]):
        """Corrects the given index to index into represented part of DBM."""
        row, col = index_tuple
        if row // 2 * 2 + 1 < col:
            return col ^ 1, row ^ 1
        else:
            return row, col

    @staticmethod
    def _col_index_limit(row):
        """Returns the column index limit (exclusive) for a given row."""
        return row // 2 * 2 + 1

    def keys(self):
        row = 0
        col = 0
        while row < self.size:
            current_index = row, col  # make a copy (as a index tuple)

            col += 1
            if col > self._col_index_limit(row):
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

    def _set_diagonal_zero(self):
        for i in range(self.size):
            self[i, i] = 0
        return self

    def _shortest_path_closure(self):
        """Uses Floyd-Warshall Algorithm to calculate shortest-path closure.
        """

        self._set_diagonal_zero()
        for k in range(self.size):
            for i in range(self.size):
                for j in range(self._col_index_limit(i)):  # optimized to not set upper right diagonal entries
                    self[i, j] = min(self[i, j], self[i, k] + self[k, j])

    @abstractmethod
    def close(self):
        """Calculates closure and sets internal representation matrix to closed canonical form if possible.
        
        If no canonical form is existent, the internal representation may stay in a unclosed form and this method 
        returns `False`. 
        
        Depending on the exact type of this CDBM, this may implement a strong (e.g. for floats) or a tight (e.g. for 
        Integers) closure.
         
        :return: `True`, iff closure successful, i.e. iff constraint system satisfiable and closed canonical form exists
        """

    def intersection(self, other: 'CDBM') -> 'CDBM':
        return self.zip(other, min)

    def union(self, other: 'CDBM') -> 'CDBM':
        return self.zip(other, max)

    def zip(self, other: 'CDBM', f) -> 'CDBM':
        if self.size != other.size:
            raise ValueError("Can not zip DBMs with unequal sizes!")
        for key in self.keys():
            self[key] = f(self[key], other[key])
        return self

    def replace(self, other):
        self.__dict__.update(other.__dict__)
        return self

    def __str__(self):
        return "\n".join([" \t".join(map(lambda x: str(x).rjust(5), self._m[row])) for row in range(self._size)])


class IntegerCDBM(CDBM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def close(self):
        """Calculates closure and sets internal representation matrix to closed canonical form if possible.
        
        Algorithm from paper: An Improved Tight Closure Algorithm for Integer Octagonal Constraints - Roberto 
        Bagnara, Patricia M. Hill, Enea Zaffanella 
        """
        self._shortest_path_closure()

        # check for Q-consistency
        for i in range(self.size):
            if self[i, i] < 0:
                return False

        # Tightening
        for i in range(self.size):
            ii = (i, i ^ 1)
            self[ii] = nan2inf(self[ii] // 2 * 2)  # NOTE: corrected error from paper

        # check for Z-consistency
        for i in range(self.size):
            for j in range(self.size):
                if self[i, j ^ 1] + self[i ^ 1, j] < 0:
                    return False

        # strong coherence
        for i in range(self.size):
            for j in range((i // 2 + 1) * 2):
                ij = (i, j)
                ii = (i, i ^ 1)
                jj = (j ^ 1, j)
                self[ij] = min(self[ij], (self[ii] + self[jj]) // 2)

        return True
