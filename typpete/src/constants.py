BUILTINS = {
    'none': ['object'],
    'complex': ['object'],
    'float': ['complex'],
    'int': ['float'],
    'bool': ['int'],
    'sequence': ['object'],
    'str': ['sequence'],
    'bytes': ['sequence'],
    'tuple': ['sequence'],
    ('list', 'list_arg_0'): ['sequence'],
    ('set', 'set_arg_0'): ['object'],
    ('dict', 'dict_arg_0', 'dict_arg_1'): ['object'],
    ('type', 'type_arg_0'): ['object'],
}

ALIASES = {
    'Dict': 'dict',
    'Set': 'set',
    'List': 'list',
    'str': 'str'
}