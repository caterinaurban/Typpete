from abc import ABCMeta, abstractmethod
from enum import Enum, IntEnum
from typing import Set, Sequence

"""
Expressions.
https://docs.python.org/3.4/reference/expressions.html
"""


class Expression(metaclass=ABCMeta):
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

    def ids(self) -> Set['Expression']:
        """Identifiers that appear in the expression.
        
        :return: set of identifiers that appear in the expression
        """
        from core.expressions_tools import walk
        ids = set()
        for e in walk(self):
            if isinstance(e, VariableIdentifier):
                ids.add(e)
        return ids


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
        if issubclass(self.typ, str):
            return f'"{self.val}"'
        else:
            return f'{self.val}'


class Input(Expression):
    def __init__(self, typ):
        """Input expression representation.

        :param typ: type of the input
        """
        super().__init__(typ)

    def __eq__(self, other):
        return self.typ == other.typ

    def __hash__(self):
        return hash(self.typ)

    def __str__(self):
        return 'input()'


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


class VariableIdentifier(Identifier):
    def __init__(self, typ, name: str):
        """Variable identifier expression representation.
        
        :param typ: type of the identifier
        :param name: name of the identifier
        """
        super().__init__(typ, name)


class ListDisplay(Expression):
    """List display
    
    https://docs.python.org/3/reference/expressions.html#list-displays
    """

    def __init__(self, typ=type(list), items: Sequence = None):
        """List display representation
        
        :param typ: type of the list display
        :param items: listed items
        """
        super().__init__(typ)
        self._items = items or []

    @property
    def items(self):
        return self._items

    def __eq__(self, other):
        return (self.typ, self.items) == (other.typ, other.items)

    def __hash__(self):
        return hash((self.typ, str(self.items)))

    def __str__(self):
        return str(self.items)


"""
Primary Expressions
https://docs.python.org/3.4/reference/expressions.html#primaries
"""


class AttributeReference(Expression):
    """Attribute reference expression representation.

    https://docs.python.org/3.4/reference/expressions.html#attribute-references
    """

    def __init__(self, typ, primary: Expression, attribute: Identifier):
        """Attribute reference expression representation.
        
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


class Slice(Expression):
    """Slice (list/dictionary access) representation.
    """

    def __init__(self, typ, target: Expression, lower: Expression, step: Expression, upper: Expression):
        """Slice (list/dictionary access) representation.

        :param typ: type of the slice
        :param target
        :param lower
        :param upper
        :param step
        """
        super().__init__(typ)
        self._target = target
        self._lower = lower
        self._step = step
        self._upper = upper

    @property
    def target(self):
        return self._target

    @property
    def lower(self):
        return self._lower

    @property
    def step(self):
        return self._step

    @property
    def upper(self):
        return self._upper

    def __str__(self):
        if self.step:
            return "{}[{}:{}:{}]".format(self.target or "", self.lower, self.step, self.upper or "")
        else:
            return "{}[{}:{}]".format(self.target, self.lower or "", self.upper or "")

    def __eq__(self, other):
        return (self.typ, self.target, self.lower, self.step, self.upper) == (
            other.typ, other.target, other.lower, self.step, self.upper)

    def __hash__(self):
        return hash((self.typ, self.target, self.lower, self.step, self.upper))


class Index(Expression):
    """Index (list/dictionary access) representation.
    """

    def __init__(self, typ, target: Expression, index: Expression):
        """Index  (list/dictionary access) representation.

        :param typ: type of the attribute
        :param target
        :param index
        """
        super().__init__(typ)
        self._target = target
        self._index = index

    @property
    def target(self):
        return self._target

    @property
    def index(self):
        return self._index

    def __str__(self):
        return "{}[{}]".format(self.target, self.index)

    def __eq__(self, other):
        return (self.typ, self.target, self.index) == (
            other.typ, other.target, other.index)

    def __hash__(self):
        return hash((self.typ, self.target, self.index))


"""
Unary Operation Expressions
"""


class UnaryOperation(Expression):
    class Operator(IntEnum):
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
        return f"{str(self.operator)}({self.expression})"


class UnaryArithmeticOperation(UnaryOperation):
    """Unary arithmetic operation expression representation.
    
    https://docs.python.org/3.4/reference/expressions.html#unary-arithmetic-and-bitwise-operations
    """

    class Operator(UnaryOperation.Operator):
        """Unary arithmetic operator representation."""
        Add = 1
        Sub = -1

        def __str__(self):
            if self.value == 1:
                return "+"
            elif self.value == -1:
                return "-"

    def __init__(self, typ, operator: Operator, expression: Expression):
        """Unary arithmetic operation expression representation.
        
        :param typ: type of the operation
        :param operator: operator of the operation
        :param expression: expression of the operation 
        """
        super().__init__(typ, operator, expression)


class UnaryBooleanOperation(UnaryOperation):
    """Unary boolean operation expression representation.
    
    https://docs.python.org/3.4/reference/expressions.html#boolean-operations
    """

    class Operator(UnaryOperation.Operator):
        """Unary boolean operator representation."""
        Neg = 1

        def __str__(self):
            if self.value == 1:
                return "not"

    def __init__(self, typ, operator: Operator, expression: Expression):
        """Unary boolean operation expression representation.
        
        :param typ: type of the operation
        :param operator: operator of the operation
        :param expression: expression of the operation 
        """
        super().__init__(typ, operator, expression)


"""
Binary Operation Expressions
"""


class BinaryOperation(Expression):
    class Operator(IntEnum):
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
        return f"({self.left} {str(self.operator)} {self.right})"


class BinaryArithmeticOperation(BinaryOperation):
    """Binary arithmetic operation expression representation.
    
    https://docs.python.org/3.4/reference/expressions.html#binary-arithmetic-operations
    """

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
        
        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)


class BinaryBooleanOperation(BinaryOperation):
    """Binary boolean operation expression representation.
    
    https://docs.python.org/3.6/reference/expressions.html#boolean-operations
    """

    class Operator(BinaryOperation.Operator):
        """Binary arithmetic operator representation."""
        And = 1
        Or = 2
        Xor = 3

        def __str__(self):
            return self.name.lower()

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary boolean operation expression representation.

        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)


class BinaryComparisonOperation(BinaryOperation):
    """Binary comparison operation expression representation.
    
    https://docs.python.org/3.4/reference/expressions.html#comparisons
    """

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

        def reverse_operator(self):
            """Returns the reverse operator of this operator."""
            try:
                return BinaryComparisonOperation.Operator.REVERSE_OPERATOR[self]
            except KeyError:
                return None

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

    Operator.REVERSE_OPERATOR = {
        Operator.Eq: Operator.NotEq,
        Operator.NotEq: Operator.Eq,
        Operator.Lt: Operator.GtE,
        Operator.LtE: Operator.Gt,
        Operator.Gt: Operator.LtE,
        Operator.GtE: Operator.Lt,
        Operator.Is: Operator.IsNot,
        Operator.IsNot: Operator.Is,
        Operator.In: Operator.NotIn,
        Operator.NotIn: Operator.In
    }

    def __init__(self, typ, left: Expression, operator: Operator, right: Expression):
        """Binary comparison operation expression representation.

        :param typ: type of the operation
        :param left: left expression of the operation
        :param operator: operator of the operation
        :param right: right expression of the operation
        """
        super().__init__(typ, left, operator, right)
