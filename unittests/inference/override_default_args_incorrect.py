class A:
    def f(self, x=1):
        pass

class B(A):
    def f(self, x):
        pass

# throws TypeError