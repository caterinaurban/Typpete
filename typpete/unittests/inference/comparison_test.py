class A:
    def __init__(self, x):
        self.x = 1

    def __gt__(self, other):
        return self.x > other.x

    def __lt__(self, other):
        return self.x < other.x

    def __ge__(self, other):
        return self.x >= other.x

    def __le__(self, other):
        return self.x <= other.x


a1 = A(1)
a2 = A(2)

b3 = a1 > a2
b4 = a1 >= a2
b5 = a1 < a2
b6 = a1 <= a2

b7 = "" > ""
b8 = 1 > 1
b9 = [1,2,3] > [4,6]
b10 = {1} >= {3}