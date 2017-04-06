from abc import ABC, abstractmethod


class Expression(ABC):
    def __init__(self, typ):
        """Expression representation. 
        Expressions represent values returned by statements.
        
        :param typ: type of the expression 
        """
        self._typ = typ

    @property
    def typ(self):
        return self._typ

    def __ne__(self, other: 'Expression'):
        return not (self == other)

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
        self._val = val

    @property
    def val(self):
        return self._val

    def __eq__(self, other: 'Constant'):
        return (self.typ, self.val) == (other.typ, other.val)

    def __hash__(self):
        return hash((self.typ, self.val))

    def __str__(self):
        return self.val


class Identifier(Expression):
    def __init__(self, typ, name: str):
        """Identifier expression.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ)
        self._name = name

    @property
    def name(self):
        return self._name

    def __eq__(self, other: 'Identifier'):
        return (self.typ, self.name) == (other.typ, other.name)

    def __hash__(self):
        return hash((self.typ, self.name))

    def __str__(self):
        return self.name


class VariableIdentifier(Identifier):
    def __init__(self, typ, name: str):
        """Variable identifier expression.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ, name)
