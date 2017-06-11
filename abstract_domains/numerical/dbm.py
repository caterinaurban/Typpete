from abc import ABCMeta, abstractmethod
from math import inf, nan, isinf, isnan
from typing import Tuple


def nan2inf(f):
    return inf if isnan(f) else f


class CDBM(metaclass=ABCMeta):
    """Coherent Difference Bound Matrix.
    
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

        for i in range(self.size):
            self[i, i] = 0

    @property
    def size(self):
        return self._size

    @property
    def strongly_closed(self):
        triang_eq = all([self[i, j] <= self[i, k] + self[k, j]
                         for i in range(self.size) for j in range(self.size) for k in range(self.size)])
        print([self[i, j] <= self[i, k] + self[k, j]
               for i in range(self.size) for j in range(self.size) for k in range(self.size)])
        for i in range(self.size):
            for j in range(self.size):
                for k in range(self.size):
                    if not self[i, j] <= self[i, k] + self[k, j]:
                        print(f"{self[i, j]} !<= {self[i, k]} + {self[k, j]} \t ({i},{j}) !<= ({i},{k}) + ({k},{j})")
        cond = all([self[i, j] <= nan2inf((self[i, i ^ 1] + self[j ^ 1, j]) // 2)
                    for i in range(self.size) for j in range(self.size)])
        diag_zero = all([self[i, i] == 0 for i in range(self.size)])
        print(f"triang_eq={triang_eq}, cond={cond}, diag_zero={diag_zero}")
        return triang_eq and cond and diag_zero

    @property
    def tightly_closed(self):
        unary_cond_tight = all([isinf(self[i, i ^ 1]) or self[i, i ^ 1] % 2 == 0 for i in range(self.size)])
        print(f"unary_cond_tight={unary_cond_tight}")
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

    @abstractmethod
    def close(self):
        """Calculates closure and sets internal representation matrix to closed canonical form.
        
        Depending on the exact type of this CDBM, this may implement a strong (e.g. for floats) or a tight (e.g. for Integers) closure.
        """

    @abstractmethod
    def close_element(self, row, col):
        """Calculates one step of incremental closure and sets internal representation matrix to closed canonical form.
        
        **NOTE**: this method only works correctly if only the element at (row, col)
        (in the reduced representation - corresponds to 2 coherent elements in the full matrix)
        differs from a closed form matrix.
        """

    def replace(self, other):
        self.__dict__.update(other.__dict__)
        return self

    def __str__(self):
        return "\n".join([" \t".join(map(lambda x: str(x).rjust(5), self._m[row])) for row in range(self._size)])


class IntegerCDBM(CDBM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def close(self):
        work_dbm = IntegerCDBM(self.size)  # create default=top DBM (all elements set to inf, diagonal to zero)
        for i in range(self.size):
            for j in range((i // 2 + 1) * 2):
                if i != j and self[i, j] < inf:  # ignore diagonal elements and unset conditions (inf)
                    work_dbm[i, j] = self[i, j]
                    print("WORK_DBM")
                    print(work_dbm)
                    work_dbm.close_element(i, j)
                    print("WORK_DBM AFTER CLOSE")
                    print(work_dbm)

        return self.replace(work_dbm)

    def close_element(self, row, col):
        # compute indices involving r and c
        rc = (row, col)
        rr = (row ^ 1, row)
        cc = (col, col ^ 1)

        # loop through rows
        for i in range(self.size):
            # compute indices involving i
            ir = (i, row)
            ic = (i, col ^ 1)
            ci = (col, i ^ 1)
            # loop through columns
            for j in range((i // 2 + 1) * 2):
                # compute indices involving j
                ij = (i, j)
                cj = (col, j)
                rj = (row ^ 1, j)
                # first update step
                if i == (j ^ 1):
                    self[ij] = min(self[ij], 2 * self[rc] + 2 * self[ic] + self[rr])
                    self[ij] = min(self[ij], 2 * self[rc] + 2 * self[ir] + self[cc])
                    self[ij] = min(self[ij], (self[ir] + self[rc] + self[ci]) // 2 * 2)
                else:
                    self[ij] = min(self[ij], self[ir] + self[rc] + self[cj])
                    self[ij] = min(self[ij], self[ic] + self[rc] + self[rj])

        # loop through rows and columns
        for i in range(self.size):
            for j in range((i // 2 + 1) * 2):
                # compute indices involving i and j
                ij = (i, j)
                ii = (i, i ^ 1)
                jj = (j ^ 1, j)
                # second update step
                self[ij] = min(self[ij], (self[ii] + self[jj]) // 2)
