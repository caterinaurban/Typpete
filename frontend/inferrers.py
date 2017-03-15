from abc import ABCMeta, abstractmethod

class Inferrer(metaclass=ABCMeta):
    """This class is the base inferrer for all inferrer types."""

    @abstractmethod
    def infer(self, node, context):
        """Infers the type of the AST node.

        This is an abstract method, that is meant to be overridden by the subclasses of this class.

        Arguments:
            node (ast.Node): AST node whose type is to be inferred.
            context (Context): The parent context mapping variables to their types.

        Returns:
            (Type): The inferred type of the node.
        """
        pass


class ExprInferrer(Inferrer):
    """Inferrer for python expressions.

    Infers the types for the following expressions:
         - BinOp(expr left, operator op, expr right)
         - UnaryOp(unaryop op, expr operand)
         - Lambda(arguments args, expr body)
         - IfExp(expr test, expr body, expr orelse)
         - Dict(expr* keys, expr* values)
         - Set(expr* elts)
         - ListComp(expr elt, comprehension* generators)
         - SetComp(expr elt, comprehension* generators)
         - DictComp(expr key, expr value, comprehension* generators)
         - GeneratorExp(expr elt, comprehension* generators)
         - Await(expr value)
         - Yield(expr? value)
         - YieldFrom(expr value)
         - Compare(expr left, cmpop* ops, expr* comparators)
         - Call(expr func, expr* args, keyword* keywords)
         - Num(object n) -- a number as a PyObject.
         - Str(string s) -- need to specify raw, unicode, etc?
         - FormattedValue(expr value, int? conversion, expr? format_spec)
         - JoinedStr(expr* values)
         - Bytes(bytes s)
         - NameConstant(singleton value)
         - Ellipsis
         - Constant(constant value)
         - Attribute(expr value, identifier attr, expr_context ctx)
         - Subscript(expr value, slice slice, expr_context ctx)
         - Starred(expr value, expr_context ctx)
         - Name(identifier id, expr_context ctx)
         - List(expr* elts, expr_context ctx)
         - Tuple(expr* elts, expr_context ctx)
    """

    def infer(self, node, context):
        # TODO: implement inference function
        return
