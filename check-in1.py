import functions
from functions import *


def test_input_file(filename):
	ast = parse_file(filename)
	vs = NodeVisitor()
	vs.visit(ast)
	print("Testing on code block " + filename)
	allvars, written = get_vars_and_written(vs)
	print("ALL VARIABLES: ", allvars)
	print("ALL WRITTEN VARIABLES: ", written)

if __name__ == "__main__":
	test_input_file('./project3inputs/p3_input1')
	test_input_file('./project3inputs/p3_input2')
	test_input_file('./project3inputs/p3_input3')