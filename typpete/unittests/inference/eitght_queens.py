BOARD_SIZE = 8


class BailOut:
    pass


def validate(q):
    left = right = col = q[-1]
    for r in reversed(q[:-1]):
        left, right = left-1, right+1
        if r in (left, col, right):
            raise BailOut


def add_queen(q):
    for i in range(BOARD_SIZE):
        test_queens = q + [i]
        validate(test_queens)
        if len(test_queens) == BOARD_SIZE:
            return test_queens
        else:
            return add_queen(test_queens)
    return []

queens = add_queen([])
print(queens)
print("\n".join([". "*q + "Q " + ". "*(BOARD_SIZE-q-1) for q in queens]))


# BOARD_SIZE := int
# BailOut := Type[BailOut]
# add_queen := Callable[[List[int]], List[int]]
# queens := List[int]
# validate := Callable[[List[int]], None]
