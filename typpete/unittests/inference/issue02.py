from abc import ABCMeta, abstractmethod

class Aexp(ABCMeta):
    @abstractmethod
    def eval(self, env):
        pass

class IntAexp(Aexp):
    def __init__(self, i):
        self.i = i

    def eval(self, env):
        return self.i

class BinopAexp(Aexp):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        if self.op == '/':
            value = left_value / right_value
            return value
        else:
            raise RuntimeError('unknown operator: ' + self.op)

class Statement(metaclass=ABCMeta):
    @abstractmethod
    def eval(self, env):
        pass

class AssignStatement(Statement):
    def __init__(self, name, aexp):
        self.name = name
        self.aexp = aexp

    def eval(self, env):
        value = self.aexp.eval(env)
        env[self.name] = value

"""
x = 0
x = 1 / 2
"""

env = dict()
i = AssignStatement('x', IntAexp(0))
d = BinopAexp('/', IntAexp(1), IntAexp(2))
f = d.eval(env)
a = AssignStatement('x', d)
a.eval(env)
print(env)

# env := Dict[str, float]
# i := AssignStatement
# d := BinopAexp
# f := float
# a := AssignStatement

