from typing import List, Union

from core.expressions import Expression, BinaryArithmeticOperation, Operation


class VariadicArithmeticOperation(Operation):
    def __init__(self, typ, operator: BinaryArithmeticOperation.Operator,
                 operands: Union[List[Expression], type(None)] = None):
        """Variadic arithmetic operation.
        
        E.g. the sum over arbitrary many summands (expressions).

        :param typ: type of the operation
        :param operator: operator of the operation
        :param operands: list of expressions the operator is applied to
        """
        super().__init__(typ)
        self._operator = operator
        self._operands = operands or []

    @property
    def operator(self):
        return self._operator

    @property
    def operands(self):
        return self._operands

    @operands.setter
    def operands(self, expressions):
        self._operands = expressions

    def __eq__(self, other):
        return (self.typ, self.operator, self.operands) == (other.typ, other.operator, other.operands)

    def __hash__(self):
        return hash((self.typ, self.operator, self.operands))

    def __str__(self):
        string_list = [f"({str(operand)})" if isinstance(operand, Operation) else str(operand) for operand in
                       self.operands]
        return str(f" {str(self.operator)} ").join(string_list)
