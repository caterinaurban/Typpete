class Aexp:
    def eval(self, env):
        return 0


class IntAexp(Aexp):
    def __init__(self, i):
        self.i = i

    def __repr__(self):
        return 'IntAexp(%d)' % self.i

    def eval(self, env):
        return self.i


class VarAexp(Aexp):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'VarAexp(%s)' % self.name

    def eval(self, env):
        if self.name in env:
            return env[self.name]
        else:
            return 0


class BinopAexp(Aexp):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return 'BinopAexp(%s, %s, %s)' % (self.op, self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        if self.op == '+':
            value = left_value + right_value
            return value
        elif self.op == '-':
            value = left_value - right_value
            return value
        elif self.op == '*':
            value = left_value * right_value
            return value
        elif self.op == '/':
            value = left_value / right_value
            return value
        else:
            raise RuntimeError('unknown operator: ' + self.op)


class Bexp:
    pass


class RelopBexp(Bexp):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def __repr__(self):
        return 'RelopBexp(%s, %s, %s)' % (self.op, self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        if self.op == '<':
            value = left_value < right_value
            return value
        elif self.op == '<=':
            value = left_value <= right_value
            return value
        elif self.op == '>':
            value = left_value > right_value
            return value
        elif self.op == '>=':
            value = left_value >= right_value
            return value
        elif self.op == '=':
            value = left_value == right_value
            return value
        elif self.op == '!=':
            value = left_value != right_value
            return value
        else:
            raise RuntimeError('unknown operator: ' + self.op)


class AndBexp(Bexp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'AndBexp(%s, %s)' % (self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        return left_value and right_value


class OrBexp(Bexp):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return 'OrBexp(%s, %s)' % (self.left, self.right)

    def eval(self, env):
        left_value = self.left.eval(env)
        right_value = self.right.eval(env)
        return left_value or right_value


class NotBexp(Bexp):
    def __init__(self, exp):
        self.exp = exp

    def __repr__(self):
        return 'NotBexp(%s)' % self.exp

    def eval(self, env):
        value = self.exp.eval(env)
        return not value


class Statement:
    def eval(self, env):
        pass


class AssignStatement(Statement):
    def __init__(self, name, aexp):
        self.name = name
        self.aexp = aexp

    def __repr__(self):
        return 'AssignStatement(%s, %s)' % (self.name, self.aexp)

    def eval(self, env):
        value = self.aexp.eval(env)
        env[self.name] = value


class CompoundStatement(Statement):
    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __repr__(self):
        return 'CompoundStatement(%s, %s)' % (self.first, self.second)

    def eval(self, env):
        self.first.eval(env)
        self.second.eval(env)


class IfStatement(Statement):
    def __init__(self, condition, true_stmt, false_stmt):
        self.condition = condition
        self.true_stmt = true_stmt
        self.false_stmt = false_stmt

    def __repr__(self):
        return 'IfStatement(%s, %s, %s)' % (self.condition, self.true_stmt, self.false_stmt)

    def eval(self, env):
        condition_value = self.condition.eval(env)
        if condition_value:
            self.true_stmt.eval(env)
        else:
            if self.false_stmt:
                self.false_stmt.eval(env)


class WhileStatement(Statement):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def __repr__(self):
        return 'WhileStatement(%s, %s)' % (self.condition, self.body)

    def eval(self, env):
        condition_value = self.condition.eval(env)
        while condition_value:
            self.body.eval(env)
            condition_value = self.condition.eval(env)


"""
x = 0
while x < 10:
    x = x + 1
"""
env = dict()
x = VarAexp('x')
z = IntAexp(0)
i = AssignStatement('x', z)
t = IntAexp(10)
c = RelopBexp('<', x, t)
o = IntAexp(1)
r = BinopAexp('+', x, o)
a = AssignStatement('x', r)
w = WhileStatement(c, a)
p = CompoundStatement(i, w)
p.eval(env)
print(env)


# Aexp := Type[Aexp]
# IntAexp := Type[IntAexp]
# VarAexp := Type[VarAexp]
# BinopAexp := Type[BinopAexp]

# Bexp := Type[Bexp]
# RelopBexp := Type[RelopBexp]
# AndBexp := Type[AndBexp]
# OrBexp := Type[OrBexp]
# NotBexp := Type[NotBexp]

# Statement := Type[Statement]
# AssignStatement := Type[AssignStatement]
# CompoundStatement := Type[CompoundStatement]
# IfStatement := Type[IfStatement]
# WhileStatement := Type[WhileStatement]

# env := Dict[str, int]
# x := VarAexp
# z := IntAexp
# i := AssignStatement
# t := IntAexp
# c := RelopBexp
# o := IntAexp
# r := BinopAexp
# a := AssignStatement
# w := WhileStatement
# p := CompoundStatement
