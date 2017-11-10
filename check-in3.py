from pycparser import parse_file, c_ast
import functions
from functions import *
import minic.c_ast_to_minic as ctoc
import minic.minic_ast as mc
import func_ast as fast
from minic.mutils import lmap
#TODO: CLEAN UP IMPORTS

# HELPER FUNCTIONS COPIED FROM c_ast_to_minic.py
def unsupported(y):
    if y is None:
        print("unsuported called with None")
        return None
    else:
        print("unsuported called on ", y, " error")
        print(y.__class__)

# Checks that the original construct is a value, a not any another construct. It helps
# in checking that we have terminal symbols at the right places.
def v(orig):
    if isinstance(orig, str) or isinstance(orig, int) or isinstance(orig, float) \
            or isinstance(orig, bool) or orig is None:
        return orig
    else:
        print("Unexpected type for value %r" % orig)
        raise TypeError

def tmap(x):
    if isinstance(x, list):
        return lmap(transform_ctf, x)
    else:
        return transform_ctf(x)
# HELPER FUNCTIONS COPIED FROM c_ast_to_minic.py



def transform_ctf(x):
    """
    Transform function from minic to our function representation
    Currently Supports:
        Constants
        Decl
        ID
        Binary
        Assignments
        Unary
    """
    return {
        # constant ... = 5;
        mc.Constant: (lambda orig: fast.Constant(v(orig.value), coord=orig.coord)),
        # ... = x;
        mc.ID: (lambda orig: fast.ID(v(orig.name))),
        # ... = (left) op (right)
        mc.BinaryOp: (lambda orig: fast.BinaryOp(v(orig.op), transform_ctf(orig.left), transform_ctf(orig.right), coord=orig.coord)),

        # int x = ...
        mc.Decl: (lambda orig: fast.Let(transform_ctf(orig.name), transform_ctf(orig.init), coord=orig.coord)),
        # x = ...
        mc.Assignment: (lambda orig: fast.Let(transform_ctf(orig.lvalue), transform_ctf(orig.rvalue), coord=orig.coord)),

        str: (lambda orig: orig),
        int: (lambda orig: orig),
        float: (lambda orig: orig),
        list: (lambda orig: tmap(orig)),
    }.get(x.__class__, lambda y: unsupported(y))(x)


class BlockVisitor(mast.NodeVisitor):

    def __init__(self):
        self.functional_code = []


    def visit_Block(self, node):
        """
        For each block of code, convert to a functional representation
        ie: every block becomes a function
        """
        new_function = block_converter(node)
        self.functional_code.append(new_function)


def block_converter(block):
    """
    Converts minic_ast.Block to func_fast.functionDef
    """

    # Find all relevant vars for func input and output
    nvs = NodeVisitor()
    nvs.visit(block)
    input_args, output_args = get_vars_and_written(nvs)

    # update the helper to make the function header
    # currently does not produce correct behabiour
        # 1.
            # int a = q;
            # we dont list q as a required input var from get_vars_and_written()

    # get all declarations, assignments, etc in the block
    block_items = block.block_items

    # transform them to our functional representation
    func_block_items = [transform_ctf(i) for i in block_items]
    func_def = fast.functionDef(input_args, output_args, func_block_items)

    return func_def


# Testing the code
ast = parse_file('./project3inputs/p3_input4')
minic_ast = ctoc.transform(ast)
vs = BlockVisitor()
vs.visit(minic_ast)

for function in vs.functional_code:
    print(function)
