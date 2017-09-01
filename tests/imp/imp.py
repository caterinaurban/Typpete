import sys
from imp_parser import *
from imp_lexer import *

from typing import TypeVar, Type

T = TypeVar("T")

def Cast(x: object, y: Type[T]) -> T: ...

def usage():
    sys.stderr.write('Usage: imp filename\n')
    sys.exit(1)


if len(sys.argv) != 2:
    usage()
filename = sys.argv[1]
text = ""
tokens = imp_lex(text)
parse_result = imp_parse(tokens)
if not parse_result:
    sys.stderr.write('Parse error!\n')
    sys.exit(1)
ast = Cast(parse_result.value, Equality)
#ast = parse_result.value
env = {}
ast.eval(env)

sys.stdout.write('Final variable values:\n')
for name in env:
    sys.stdout.write('%s: %s\n' % (name, env[name]))