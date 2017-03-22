from abc import ABCMeta, abstractmethod

class Type(metaclass=ABCMeta):
    """This class is the top-parent of all possible inferred types of a Python program.
    Every type has its own class that inherits this class.
    """

    @abstractmethod
    def is_subtype(self, t):
        """Check if this type is a subtype of the parameter type.

        Arguments:
            type (Type): The type to check the subtype relationship against.
        """
        pass


    @abstractmethod
    def get_name(self):
        """Get the name of the type"""
        pass

    # Two types are considered identical if their names exactly match.
    def __eq__(self, other):
        return self.get_name() == other.get_name()

    def __hash__(self):
        return hash(self.get_name())

class TNone(Type):

    def is_subtype(self, t):
        return True

    def get_name(self):
        return "None"

# TODO: Numerics should be subtype of class
class TBool(Type):

    def is_subtype(self, t):
        return isinstance(t, (TBool, TInt, TFloat))

    def get_name(self):
        return "Bool"


class TInt(Type):

    def is_subtype(self, t):
        return isinstance(t, (TInt, TFloat))

    def get_name(self):
        return "Int"


class TFloat(Type):

    def is_subtype(self, t):
        return isinstance(t, TFloat)

    def get_name(self):
        return "Float"


class TString(Type):

    def is_subtype(self, t):
        return isinstance(t, TString)

    def get_name(self):
        return "String"


class TBytesString(Type):

    def is_subtype(self, t):
        return isinstance(t, TBytesString)

    def get_name(self):
        return "ByteString"


class TList(Type):
    """Type given to homogeneous lists.

    Attributes:
        type (Type): Type of the list elements
    """

    def __init__(self, t):
        self.type = t

    def is_subtype(self, t):
        return isinstance(t, TList) and type(self.type) is type(t.type)

    def get_name(self):
        return "List[{}]".format(self.type.get_name())


class TTuple(Type):
    """Type given to a tuple.

    Attributes:
        types ([Type]): Types of the tuple elements.
    """

    def __init__(self, t):
        self.types = t

    def is_subtype(self, t):
        if not isinstance(t, TTuple):
            return False
        if len(self.types) != len(t.types):
            return False
        for i in range(len(self.types)):
            if not self.types[i].is_subtype(t.types[i]):
                return False
        return True

    def get_name(self):
        types_names = [t.get_name() for t in self.types]
        return "Tuple({})".format(",".join(types_names))

    def get_possible_tuple_slicings(self):
        """Returns a union type of all possible slicings of this tuple

		For example:
			t = (1, "string", 2.5)

			t.get_possible_tuple_slicings() will return the following
			Union{Tuple(Int), Tuple(Int,String), Tuple(Int,String,Float), Tuple(String), Tuple(String,Float), Tuple(Float), Tuple()}

		"""
        slicings = {TTuple([])}
        for i in range(len(self.types)):
            for j in range(i + 1, len(self.types) + 1):
                slicings.add(TTuple(self.types[i:j]))
        return UnionTypes(slicings)

class TIterator(Type):
    """Type given to an iterator.

    Attributes:
        type (Type): Type of the iterator.
    """

    def __init__(self, t):
        self.type = t

    def is_subtype(self, t):
        return isinstance(t, TIterator) and type(self.type) is type(t.type)

    def get_name(self):
        return "Iterator({})".format(self.type.get_name())


class TDictionary(Type):
    """Type given to a dictionary, whose keys are of the same type, and values are of the same type.

    Attributes:
        key_type (Type): Type of the dictionary keys.
        value_type (Type): Type of the dictionary values.
    """

    def __init__(self, t_k, t_v):
        self.key_type = t_k
        self.value_type = t_v

    def is_subtype(self, t):
        return (isinstance(t, TDictionary) and type(self.key_type) is type(t.key_type)
            and type(self.value_type) is type(t.value_type))

    def get_name(self):
        return "Dict({}:{})".format(self.key_type.get_name(), self.value_type.get_name())


class TSet(Type):
    """Type given to homogeneous sets"""

    def __init__(self, t):
        self.type = t

    def is_subtype(self, t):
        return isinstance(t, TSet) and self.type.is_subtype(t.type)

    def get_name(self):
        return "Set({})".format(self.type.get_name())


class TFunction(Type):
    """Type given to a function.

    Attributes:
        return_type (Type): Type of the function return value.
        arg_types ([Type]): A list of types for the function arguments.
    """

    def __init__(self, t_r, t_a):
        self.return_type = t_r
        self.arg_types = t_a

    def is_subtype(self, t):
        if not isinstance(t, TFunction):
            return False
        if len(self.arg_types) != len(t.arg_types):
            return False
        if not self.return_type.is_subtype(t.return_type):
            return False
        for i in range(len(self.arg_types)):
            if not t.arg_types[i].is_subtype(self.arg_types[i]):
                return False
        return True

    def get_name(self):
        args_types_names = [t.get_name() for t in self.arg_types]
        return "Function({}) --> {}".format(",".join(args_types_names), self.return_type.get_name())


class UnionTypes(Type):
    """Type given to variables that are inferred to have a range of types.

    Attributes:
        types (set{Type}): An unordered set of possible types.
    """

    def __init__(self, t=set()):
        self.types = set()
        for ti in t:
            self.union(ti)

    def is_subtype(self, t):
        if len(self.types) == 1: # return true if there's only one type in the set, and this type is a subtype of the passed argument
            unique_type = list(self.types)[0]
            if unique_type.is_subtype(t):
                return True
        if not isinstance(t, UnionTypes):
            return False
        for m_t in self.types: # look for a supertype in t.types for every type in self.types
            found_supertype = False
            for t_t in t.types:
                if m_t.is_subtype(t_t):
                    found_supertype = True
                    break
            if not found_supertype:
                return False

        return True

    def get_name(self):
        types_names = [t.get_name() for t in self.types]
        return "Union{{{}}}".format(",".join(types_names))

    def union(self, other_type):
        """Add other types to the union"""
        if isinstance(other_type, UnionTypes):
            for t in other_type.types:
                self.union(t)
        else:
            to_remove = set()
            for t in self.types:
                if other_type.is_subtype(t): # Ignore union if supertype already exists in the set
                    return
                elif t.is_subtype(other_type): # Remove subtypes of added type
                    to_remove.add(t)
            for t in to_remove:
                self.types.remove(t)
            self.types.add(other_type)


class TClass(Type):
    """Type given to a class.

    Attributes:
        context (Context): Contains a mapping between variables and types within the scope of this class.
    """

    def __init__(self, context):
        self.context = context

    def is_subtype(self, t):
        # TODO: implement
        return False


def is_subtype(type1, type2):
    """Check if type1 is a subtype of type2

    Arguments:
        type1 (Type)
        type2 (Type)

    Returns:
        True: if type1 is a subtype of type2
        False: otherwise
    """

    return type1.is_subtype(type2)
