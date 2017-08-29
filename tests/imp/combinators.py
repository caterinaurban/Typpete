class Result:
    def __init__(self, value, pos):
        self.value = value
        self.pos = pos

    def __repr__(self):
        return 'Result(%s, %d)' % (self.value, self.pos)

class Parser:
    def __add__(self, other):
        return Concat(self, other)

    def __mul__(self, other):
        return Exp(self, other)

    def __or__(self, other):
        return Alternate(self, other)

    def __xor__(self, function):
        return Process(self, function)

    def __call__(self, tokens, pos):
        pass

class Tag(Parser):
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, tokens, pos):
        if pos < len(tokens) and tokens[pos][1] is self.tag:
            return Result(tokens[pos][0], pos + 1)
        else:
            return None


class Reserved(Parser):
    def __init__(self, value, tag):
        self.value = value
        self.tag = tag

    def __call__(self, tokens, pos):
        if pos < len(tokens) and \
           tokens[pos][0] == self.value and \
           tokens[pos][1] is self.tag:
            return Result(tokens[pos][0], pos + 1)
        else:
            return None


class Concat(Parser):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, tokens, pos):
        x = self.left
        y = self.right
        left_result = x(tokens, pos)
        if left_result:
            right_result = y(tokens, left_result.pos)
            if right_result:
                combined_value = (left_result.value, right_result.value)
                return Result(combined_value, right_result.pos)
        return None

class Exp(Parser):
    def __init__(self, parser, separator):
        self.parser = parser
        self.separator = separator

    def __call__(self, tokens, pos):
        x = self.parser
        y = self.separator
        result = x(tokens, pos)

        def process_next(parsed):
            pass
        next_parser = y + x ^ process_next

        next_result = result
        while next_result:
            next_result = next_parser(tokens, result.pos)
            if next_result:
                result = next_result
        return result


class Alternate(Parser):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, tokens, pos):
        x = self.left
        y = self.right
        left_result = x(tokens, pos)
        if left_result:
            return left_result
        else:
            right_result = y(tokens, pos)
            return right_result

class Opt(Parser):
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        x = self.parser
        result = x(tokens, pos)
        if result:
            return result
        else:
            return Result(None, pos)

class Rep(Parser):
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        x = self.parser
        results = []
        result = x(tokens, pos)
        while result:
            results.append(result.value)
            pos = result.pos
            result = x(tokens, pos)
        return Result(results, pos)


class Process(Parser):
    def __init__(self, parser, function):
        self.parser = parser
        self.function = function

    def __call__(self, tokens, pos):
        x = self.parser
        y = self.function
        result = x(tokens, pos)
        if result:
            result.value = y(result.value)
            return result

class Lazy(Parser):
    def __init__(self, parser_func):
        self.parser = None
        self.parser_func = parser_func

    def __call__(self, tokens, pos):
        x = self.parser
        y = self.parser_func
        if not self.parser:
            self.parser = y()
        return x(tokens, pos)

class Phrase(Parser):
    def __init__(self, parser):
        self.parser = parser

    def __call__(self, tokens, pos):
        x = self.parser
        result = x(tokens, pos)
        if result and result.pos == len(tokens):
            return result
        else:
            return None