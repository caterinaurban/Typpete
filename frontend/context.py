class Context:
    """Represents types scope in a python program.

    Attributes:
        types_map ({str, Type}): a dict mapping variable names to their inferred types.
    """

    def __init__(self, t_m={}):
        self.types_map = t_m

    def set_type(self, var_name, var_type):
        """Sets the type of a variable in this context."""
        self.types_map[var_name] = var_type

    def has_variable(self, var_name):
        return var_name in self.types_map

    def get_variable_type(self, var_name):
        return self.types_map[var_name]
