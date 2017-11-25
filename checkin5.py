from convertc2f import *


def test_file(filename):
	ast = parse_file(filename)
	minic_ast = ctoc.transform(ast)
	vs = BlockVisitor()
	vs.visit(minic_ast)

	print("c source file can be found at: %s" % filename)

	for function in vs.functional_code:
		print(function)
		print("\n")


if __name__ == "__main__":
	print("This checking completes all the required simplificiations + more")
	print("Extra:")
	print("If a variable x is declared and used, and later redeclared but never")
	print("used again, we will remove the second declaration only and add it straight")
	print("to the output tuple.")
	print("\n")

	test_file('./project3inputs/reduction_tests/test1')
	test_file('./project3inputs/reduction_tests/test2')
	test_file('./project3inputs/reduction_tests/test3')
	test_file('./project3inputs/reduction_tests/test4')
