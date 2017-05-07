from abc import ABC, abstractmethod
from enum import Enum
from typing import Set

"""
Expressions.
https://docs.python.org/3.4/reference/expressions.html
"""


class Expression(ABC):
    def __init__(self, typ):
        """Expression representation.
        https://docs.python.org/3.4/reference/expressions.html
        
        :param typ: type of the expression 
        """
        self._typ = typ

    @property
    def typ(self):
        return self._typ

    @abstractmethod
    def __eq__(self, other: 'Expression'):
        """Expression equality.
        
        :param other: other expression to compare
        :return: whether the expression equality holds
        """

    @abstractmethod
    def __hash__(self):
        """Expression hash representation.
        
        :return: hash value representing the expression
        """

    def __ne__(self, other: 'Expression'):
        return not (self == other)

    @abstractmethod
    def __str__(self):
        """Expression string representation.
        
        :return: string representing the expression
        """

    @abstractmethod
    def ids(self) -> Set['Expression']:
        """Identifiers that appear in the expression.
        
        :return: set of identifiers that appear in the expression
        """


"""
Atomic Expressions
https://docs.python.org/3.4/reference/expressions.html#atoms
"""


class Literal(Expression):
    def __init__(self, typ, val: str):
        """Literal expression representation.
        https://docs.python.org/3.4/reference/expressions.html#literals
        
        :param typ: type of the literal
        :param val: value of the literal
        """
        super().__init__(typ)
        self._val = val

    @property
    def val(self):
        return self._val

    def __eq__(self, other):
        return (self.typ, self.val) == (other.typ, other.val)

    def __hash__(self):
        return hash((self.typ, self.val))

    def __str__(self):
        return "{0.val}".format(self)

    def ids(self) -> Set['Expression']:
        return set()


class Identifier(Expression):
    def __init__(self, typ, name: str):
        """Identifier expression representation.
        https://docs.python.org/3.4/reference/expressions.html#atom-identifiers
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ)
        self._name = name

    @property
    def name(self):
        return self._name

    def __eq__(self, other):
        return (self.typ, self.name) == (other.typ, other.name)

    def __hash__(self):
        return hash((self.typ, self.name))

    def __str__(self):
        return "{0.name}".format(self)

    def ids(self) -> Set['Expression']:
        return {self}


class VariableIdentifier(Identifier):
    def __init__(self, typ, name: str):
        """Variable identifier expression representation.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ, name)


"""
Primary Expressions
https://docs.python.org/3.4/reference/expressions.html#primaries
"""


class AttributeReference(Expression):
    def __init__(self, typ, primary: Expression, attribute: Identifier):
        """Attribute reference expression representation.
        https://docs.python.org/3.4/reference/expressions.html#attribute-references

        :param typ: type of the attribute
        :param primary: object the attribute of which is being referenced
        :param attribute: attribute being referenced
        """
        super().__init__(typ)
        self._primary = primary
        self._attribute = attribute

    @property
    def primary(self):
        return self._primary

    @property
    def attribute(self):
        return self._attribute

    def __eq__(self, other):
        return (self.typ, self.primary, self.attribute) == (other.typ, other.primary, other.attribute)

    def __hash__(self):
        return hash((self.typ, self.primary, self.attribute))

    def __str__(self):
        return "{0.primary}.{0.attribute}".format(self)

    def ids(self):
        return self.primary.ids() | self.attribute.ids()


"""
Unary Operation Expressions
"""


class UnaryOperation(Expression):
    class Operator(Enum):
        """Unary operator representation."""

        @abstractmethod
        def __str__(self):
            """Unary operator string representation.
            
            :return: string representing the operator
            """

    def __init__(self, typ, operator: Operator, expression: Expression):
        """Unary operation expression representation.
        
        :param typ: type of the operation
        :param operator: operator of the operation
        :param expression: expression of the operation 
        """
        super().__init__(typ)
        self._operator = operator
        self._expression = expression

    @property
    def operator(self):
        return self._operator

    @property
    def expression(self):
        return self._expression

    def __eq__(self, other):
        return (self.typ, self.operator, self.expression) == (other.typ, other.operator, other.expression)

    def __hash__(self):
        return hash((self.typ, self.operator, self.expression))

    def __str__(self):
        return "{0.operator}({0.expression})".format(self)

    def ids(self):
        return self.expression.ids()


class UnaryArithmeticOperation(UnaryOperation):
    class Operator(UnaryOperation.Operator):
        """Unary arithmetic operator representation."""
        Add = 1
        Sub = 2

        def __str__(self):
            if self.value == 1:
                return "+"
            elif self.value == 2:
                return "-"

    def __init__(self, typ, operator: Operator, expression: Expression):
        """Unary arithmetic operation expression representation.
        https://docs.python.org/3.4/reference/expressions.html#unary-arithmetic-and-bitwise-operations
        
        :param typ: type of the operation
        :param operator: operator of the operation
        :param expression: expression of the operation 
        """
        super().__init__(typ, operator, expression)


class UnaryBooleanOperation(UnaryOperation):
    class Operator(UnaryOperation.Operator):
        """Unary boolean operator representation."""
        Neg = 1

        def __str__(self):
            if self.value == 1:
                return "not"

    def __init__(self, typ, operator: Operator, expression: Expression):
        """Unary boolean operation expression representation.
        https://docs.python.org/3.4/reference/expressions.html#boolean-operations
        
        :param typ: type of the operation
        :param operator: operator of the operation
        :param expression: expression of the operation 
        """
        super().__init__(typ, operator, expression)


"""
Binary Operation Expressions
"""


class BinaryOperation(Expression):
    class Operator(Enum):
        """Binary operator representation."""

        @abstractmethod
        def __str__(self):
            """Binary operator string representation.

            :return: string representing the operator
            """

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary operation expression representation.
        
        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ)
        self._left = left
        self._operator = operator
        self._right = right

    @property
    def left(self):
        return self._left

    @property
    def operator(self):
        return self._operator

    @property
    def right(self):
        return self._right

    def __eq__(self, other):
        return (self.typ, self.left, self.operator, self.right) == (other.typ, other.left, other.operator, other.right)

    def __hash__(self):
        return hash((self.typ, self.left, self.operator, self.right))

    def __str__(self):
        return "{0.left} {0.operator} {0.right}".format(self)

    def ids(self) -> Set['Expression']:
        return self.left.ids() | self.right.ids()


class BinaryArithmeticOperation(BinaryOperation):
    class Operator(BinaryOperation.Operator):
        """Binary arithmetic operator representation."""
        Add = 1
        Sub = 2
        Mult = 3
        Div = 4

        def __str__(self):
            if self.value == 1:
                return "+"
            elif self.value == 2:
                return "-"
            elif self.value == 3:
                return "*"
            elif self.value == 4:
                return "/"

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary arithmetic operation expression representation.
        https://docs.python.org/3.4/reference/expressions.html#binary-arithmetic-operations
        
        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)


class BinaryBooleanOperation(BinaryOperation):
    class Operator(BinaryOperation.Operator):
        """Binary arithmetic operator representation."""
        And = 1
        Or = 2
        Xor = 3

        def __str__(self):
            return self.name.lower()

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary boolean operation expression representation.
        https://docs.python.org/3.6/reference/expressions.html#boolean-operations

        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)


class BinaryComparisonOperation(BinaryOperation):
    class Operator(BinaryOperation.Operator):
        """Binary comparison operator representation"""
        Eq = 1
        NotEq = 2
        Lt = 3
        LtE = 4
        Gt = 5
        GtE = 6
        Is = 7
        IsNot = 8
        In = 9
        NotIn = 10

        def __str__(self):
            if self.value == 1:
                return "=="
            elif self.value == 2:
                return "!="
            elif self.value == 3:
                return "<"
            elif self.value == 4:
                return "<="
            elif self.value == 5:
                return ">"
            elif self.value == 6:
                return ">="
            elif self.value == 7:
                return "is"
            elif self.value == 8:
                return "is not"
            elif self.value == 9:
                return "in"
            elif self.value == 10:
                return "not in"

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary comparison operation expression representation.
        https://docs.python.org/3.4/reference/expressions.html#comparisons

        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)
