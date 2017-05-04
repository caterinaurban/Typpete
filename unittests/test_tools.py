import io
import tokenize
import os
import re


def source_path_to_name(source_path):
    return os.path.splitext(os.path.basename(source_path))[0]


def find_result_comments(source):
    # Parse comments to find expected results
    pattern = re.compile('RESULT:?\s*(?P<result>.*)')
    for t in tokenize.tokenize(io.BytesIO(source.encode('utf-8')).readline):
        if t.type == tokenize.COMMENT:
            comment = t.string.strip("# ")
            m = pattern.match(comment)
            if m:
                expected_result = m.group('result')
                line = t.start[0]
                yield line, expected_result


def find_analysis_result_for_comments(cfg, result, line_of_comment):
    # search for analysis result of a statement with the same source line
    actual_result = None
    for node in cfg.nodes.values():
        states = result.get_node_result(node)

        for i, stmt in enumerate(node.stmts):
            if stmt.pp.line == line_of_comment:
                actual_result = states[i]
                break

        if actual_result:
            break

    if actual_result:
        return actual_result
    else:
        raise RuntimeError(
            f"No analysis result found for RESULT-comment '{comment}' at line {line}!")
