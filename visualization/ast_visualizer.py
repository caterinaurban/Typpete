import re
import optparse
import sys
from visualization.graph_renderer import GraphRenderer


def main(args):
    optparser = optparse.OptionParser(usage="python3.6 -m visualization.ast_visualizer [options] [string]")
    optparser.add_option("-f", "--file",
                         help="Read a code snippet from the specified file")
    optparser.add_option("-l", "--label",
                         help="The label for the visualization")

    options, args = optparser.parse_args(args)
    if options.file:
        with open(options.file) as instream:
            code = instream.read()
        label = options.file
    elif len(args) == 2:
        code = args[1] + "\n"
        label = "<code read from command line parameter>"
    else:
        print("Expecting Python code on stdin...")
        code = sys.stdin.read()
        label = "<code read from stdin>"
    if options.label:
        label = options.label

    code_ast = generate_pyast(code)

    renderer = GraphRenderer()
    renderer.render(code_ast, label=label)


def generate_pyast(code):
    """
    Parses the code and creates a structure of lists and dicts only.
    :param code: the code as a string
    :return: a structure of lists and dicts only, representing the ast of code
    """
    import ast
    def transform_ast(code_ast):
        if isinstance(code_ast, ast.AST):
            node = {to_camelcase(k): transform_ast(getattr(code_ast, k)) for k in code_ast._fields}
            node['node_type'] = to_camelcase(code_ast.__class__.__name__)
            return node
        elif isinstance(code_ast, list):
            return [transform_ast(el) for el in code_ast]
        else:
            return code_ast

    return transform_ast(ast.parse(code))


def to_camelcase(string):
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', string).lower()


if __name__ == '__main__':
    main(sys.argv)
