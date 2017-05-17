from frontend.pre_analysis import PreAnalyzer
import frontend.z3_types as z3_types
import ast

r = open("tests/test.py")
t = ast.parse(r.read())

analyzer = PreAnalyzer(t)

classes_data = analyzer.classes_pre_analysis()
z3_types.init_types({
    "max_tuple_length": analyzer.maximum_tuple_length(),
    "max_function_args": analyzer.maximum_function_args(),
    "classes_to_attrs": classes_data[0],
    "class_to_base": classes_data[1]
})

from frontend.stmt_inferrer import *

context = Context()
for stmt in t.body:
    infer(stmt, context)

z3_types.solver.push()
check = z3_types.solver.check()

try:
    model = z3_types.solver.model()
    for v in context.types_map:
        z3_t = context.types_map[v]
        print(z3_t)
        print("{}: {}".format(v, model[z3_t]))
except z3_types.z3types.Z3Exception as e:
    print("Check: {}".format(check))
    print(e)
