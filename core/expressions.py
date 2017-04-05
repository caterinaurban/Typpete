from abc import ABC, abstractmethod


class Expression(ABC):
    def __init__(self, typ):
        """Expression representation. 
        Expressions represent values returned by statements.
        
        :param typ: type of the expression 
        """
        self.typ = typ

    @abstractmethod
    def __str__(self):
        """Expression string representation
        
        :return: string representing the expression
        """


class Constant(Expression):
    def __init__(self, typ, val: str):
        """Constant expression value.
        
        :param typ: type of the constant
        :param val: value of the constant
        """
        super().__init__(typ)
        self.val = val

    def __str__(self):
        return self.val


class Identifier(Expression):
    def __init__(self, typ, name: str):
        """Identifier expression.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ)
        self.name = name

    def __str__(self):
        return self.name


class VariableIdentifier(Identifier):
    def __init__(self, typ, name: str):
        """Variable identifier expression.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ, name)
