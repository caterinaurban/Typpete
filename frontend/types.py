class Type(object):
    """This class is the top-parent of all possible inferred types of a Python program.
    Every type has its own class that inherits this class.
    """
    pass

class TNone(Type):
    pass

class TBool(Type):
    pass

class TInt(Type):
    pass

class TFloat(Type):
    pass

class TLong(Type):
    pass

class TString(Type):
    pass

class TList(Type):
    """Type given to homogeneous lists.

    Attributes:
        type (Type): Type of the list elements
    """

    def __init__(self, t):
        self.type = t

class TTuple(Type):
    """Type given to a tuple.

    Attributes:
        types ([Type]): Types of the tuple elements.
    """

    def __init__(self, t):
        self.types = t

class TIterator(Type):
    """Type given to an iterator.

    Attributes:
        type (Type): Type of the iterator.
    """

    def __init__(self, t):
        self.type = t

class TDictionary(Type):
    """Type given to a dictionary, whose keys are of the same type, and values are of the same type.

    Attributes:
        key_type (Type): Type of the dictionary keys.
        value_type (Type): Type of the dictionary values.
    """

    def __init__(self, t_k, t_v):
        self.key_type = t_k
        self.value_type = t_v

class TFunction(Type):
    """Type given to a function.

    Attributes:
        return_type (Type): Type of the function return value.
        arg_types ([Type]): A list of types for the function arguments.
    """

    def __init__(self, t_r, t_a):
        self.return_type = t_r
        self.arg_types = t_a

class SeveralTypes(Type):
    """Type given to variables that are inferred to have a range of types.

    Attributes:
        types ([Type]): A list of possible types.
    """

    def __init__(self, t):
        self.types = t

class TClass(Type):
    """Type given to a class.

    Attributes:
        context (Context): Contains a mapping between variables and types within the scope of this class.
    """

    def __init__(self, context):
        self.context = context

def is_subtype(type1, type2):
    """Check if type1 is a subtype of type2

    Arguments:
        type1 (Type)
        type2 (Type)

    Returns:
        True: if type1 is a subtype of type2
        False: otherwise
    """
    
    # TODO: implement
    return False
