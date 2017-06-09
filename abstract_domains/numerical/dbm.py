from math import inf


class IntegerCDBM():
    """Coherent Difference Bound Matrix
    
    A DBM-matrix `m` is *coherent* if matrix entries that represent the same condition do agree on the bound. 
    
    .. image:: _static/coherence.png
    
    **NOTE:** we use 0-based indices instead.
    
    This implies that the matrix as a special kind of symmetric. It is enough to store the lower left diagonal matrix 
    (s plus A), the diagonal (D) **plus** one more adjacent diagonal `B` to the right, which contains unary 
    conditions that may be different from the already included diagonal `A`. 
     
    ::
    
        D B x x x x
        A D B x x x
        s A D B x x
        s s A D B x
        s s s A D B
        s s s s A D
    
    
    """

    def __init__(self, size):
        self._m = []
        for i in range(size):
            row = [inf] * (i + 2)
            self._m.append(row)
