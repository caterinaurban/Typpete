from typing import List

from core.expressions import Expression, BinaryArithmeticOperation


class VariadicArithmeticOperation(Expression):
    def __init__(self, typ, operator: BinaryArithmeticOperation.Operator, expressions: List[Expression] = None):
        """Variadic arithmetic operation.
        
        E.g. the sum over arbitrary many summands (expressions).

        :param typ: type of the operation
        :param operator: operator of the operation
        :param expressions: list of expressions the operator is applied to
        """
        super().__init__(typ)
        self._operator = operator
        self._expressions = expressions or []

    @property
    def operator(self):
        return self._operator

    @property
    def expressions(self):
        return self._expressions

    @expressions.setter
    def expressions(self, expressions):
        self._expressions = expressions

    def __eq__(self, other):
        return (self.typ, self.operator, self.expressions) == (other.typ, other.operator, other.expressions)

    def __hash__(self):
        return hash((self.typ, self.operator, self.expressions))

    def __str__(self):
        return str(f" {str(self.operator)} ").join(map(str, self.expressions))
