class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, t_m={}, parent_context=None):
        self.types_map = t_m

    def get_type(self, var_name):
        if var_name in self.types_map:
            return self.types_map[var_name]
        if parent_context == None:
            raise NameError("Name {} is not defined.".format(var_name))
        return parent_context.get_type(var_name)

    def set_type(self, var_name, var_type):
        """Sets the type of a variable in this context."""
        self.types_map[var_name] = var_type

    def has_variable(self, var_name):
        return
