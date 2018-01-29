class Aexp:
    def eval(self, env):
        return 0


class IntAexp(Aexp):
    def __init__(self, i):
        self.i = i

    def eval(self, env):
        return self.i


class VarAexp(Aexp):
    def __init__(self, name):
        self.name = name

    def eval(self, env):
        if self.name in env:
            return env[self.name]
        else:
            return 0


class Statement:
    pass


class AssignStatement(Statement):
    def __init__(self, name, aexp):
        self.name = name
        self.aexp = aexp

    def eval(self, env):
        value = self.aexp.eval(env)
        env[self.name] = value

x3 = AssignStatement("x", IntAexp(3))
xy = AssignStatement("y", VarAexp("y"))
