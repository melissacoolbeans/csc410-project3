from convertc2f import *


def test_if_file(filename):
	ast = parse_file(filename)
	minic_ast = ctoc.transform(ast)
	vs = BlockVisitor()
	vs.visit(minic_ast)

	print("c source file can be found at: %s" % filename)

	for function in vs.functional_code:
		print(function)
		print("\n")


if __name__ == "__main__":
	test_if_file('./project3inputs/if_tests/test1')
	test_if_file('./project3inputs/if_tests/test2')
	test_if_file('./project3inputs/if_tests/test3')

	print("This checkin outputs exclusivly if statement tests")
	print("To see full scope of code (binary statements, etc), run other tests in project3inputs folder")
