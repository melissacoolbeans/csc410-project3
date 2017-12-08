from convertc2f import *


def test_file(filename, opt=True):
	ast = parse_file(filename)
	minic_ast = ctoc.transform(ast)
	vs = BlockVisitor()
	vs.visit(minic_ast)
	print(filename)

	for i in range(len(vs.functional_code)):

		if opt:
			print("optimized function: ")
			print(vs.opt_functional_code[i])
		else:
			print("unoptimized function: ")
			print(vs.functional_code[i])
		print("\n")
	print("\n")


if __name__ == "__main__":
	opt = True
	a = raw_input("type y for optimized code, n for unoptimized\n")
	if a == "n":
		opt = False
	f = './final_inputs/p3_input9'
	test_file(f, opt)
