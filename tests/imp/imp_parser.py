from imp_lexer import *
from combinators import *
from imp_ast import *

aexp_precedence_levels = [
    ['*', '/'],
    ['+', '-'],
]

bexp_precedence_levels = [
    ['and'],
    ['or'],
]

def keyword(kw):
    return Reserved(kw, RESERVED)

def any_operator_in_list(ops):
    op_parsers = [keyword(op) for op in ops]
    parser = op_parsers[0]

    for op in op_parsers[1:]:
        parser |= op

    return parser

def precedence(value_parser, precedence_levels, combine):
    def op_parser(precedence_level):
        return any_operator_in_list(precedence_level) ^ combine

    parser = value_parser * op_parser(precedence_levels[0])
    for precedence_level in precedence_levels[1:]:
        parser = parser * op_parser(precedence_level)
    return parser

def process_relop(parsed):
    ((left, op), right) = parsed
    return RelopBexp(op, left, right)


def process_logic(op):
    if op == 'and':
        return lambda l, r: AndBexp(l, r)
    elif op == 'or':
        return lambda l, r: OrBexp(l, r)
    else:
        raise RuntimeError('unknown logic operator: ' + op)

def process_group(parsed):
    ((a, p), b) = parsed
    return p

# Basic parsers

num = Tag(INT) ^ (lambda i: int(i))
t_id = Tag(ID)

def bexp_group():
    return keyword('(') + Lazy(bexp) + keyword(')') ^ process_group

def bexp_relop():
    relops = ['<', '<=', '>', '>=', '=', '!=']
    return aexp() + any_operator_in_list(relops) + aexp() ^ process_relop

def bexp_not():
    return keyword('not') + Lazy(bexp_term) ^ (lambda parsed: NotBexp(parsed[1]))


def bexp_term():
    return bexp_not() | \
           bexp_relop() | \
           bexp_group()

# Boolean expressions
def bexp():
    return precedence(bexp_term(),
                      bexp_precedence_levels,
                      process_logic)





def if_stmt():
    def process(parsed):
        (((((_, condition), _), true_stmt), false_parsed), _) = parsed
        if false_parsed:
            (_, false_stmt) = false_parsed
        else:
            false_stmt = None
        return IfStatement(condition, true_stmt, false_stmt)

    return keyword('if') + bexp() + \
           keyword('then') + Lazy(stmt_list) + \
           Opt(keyword('else') + Lazy(stmt_list)) + \
           keyword('end') ^ process

def assign_stmt():
    def process(parsed):
        ((name, _), exp) = parsed
        return AssignStatement(name, exp)

    return t_id + keyword(':=') + aexp() ^ process

def while_stmt():
    def process(parsed):
        ((((_, condition), _), body), _) = parsed
        return WhileStatement(condition, body)

    return keyword('while') + bexp() + \
           keyword('do') + Lazy(stmt_list) + \
           keyword('end') ^ process

def stmt():
    return assign_stmt() | \
           if_stmt() | \
           while_stmt()

# Statements
def stmt_list():
    separator = keyword(';') ^ (lambda x: lambda l, r: CompoundStatement(l, r))
    return Exp(stmt(), separator)

def parser():
    return Phrase(stmt_list())

def process_binop(op):
    return lambda l, r: BinopAexp(op, l, r)

# Top level parser
def imp_parse(tokens):
    ast = parser()(tokens, 0)
    return ast


def aexp_value():
    return (num ^ (lambda i: IntAexp(i))) | \
           (t_id ^ (lambda v: VarAexp(v)))


def aexp_group():
    return keyword('(') + Lazy(aexp) + keyword(')') ^ process_group


def aexp_term():
    return aexp_value() | aexp_group()

def aexp():
    return precedence(aexp_term(),
                      aexp_precedence_levels,
                      process_binop)















# Arithmetic expressions










# An IMP-specific combinator for binary operator expressions (aexp and bexp)



# Miscellaneous functions for binary and relational operators











# Operator keywords and precedence levels

