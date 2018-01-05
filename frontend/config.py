config = {
    # Whether to ignore the body of fully annotated functions and just take the provided types for args/return
    "ignore_fully_annotated_function": False,

    # Whether to allow different branches to use different types of same variable.
    # Example:
    # if _some_condition:
    #       x = 1
    #       x += 2
    # else:
    #       x = "string"
    #       x += "a"
    "enforce_same_type_in_branches": False,

    # List of the supported decorators for function definitions.
    "decorators": ["staticmethod"],

    # Whether to allow to define instance attribute outside __init__
    "allow_attributes_outside_init": True,

    # Whether to make None a subtype of all types
    "none_subtype_of_all": True,

    "maximum_union_length": 2,
}
