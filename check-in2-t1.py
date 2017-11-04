import functions
from functions import *
import minic.c_ast_to_minic as ctoc


def test_input_file(filename):
	ast = parse_file(filename)
	vs = NodeVisitor()
	vs.visit(ast)
	print("Testing on code block " + filename)
	args, out = get_args_and_output(vs)
	fn_proto = FunctionPrototype(args, out, filename[-9:-1])
	print(fn_proto)

if __name__ == "__main__":
	test_input_file('./project3inputs/p3_input1')
	test_input_file('./project3inputs/p3_input2')
	test_input_file('./project3inputs/p3_input3')
