from pycparser import parse_file, c_ast
import functions
from functions import *
import minic.c_ast_to_minic as ctoc
import minic.minic_ast as mc
import func_ast as fast
from minic.mutils import lmap
#TODO: CLEAN UP IMPORTS


# PRINT UNSUPPORTED
show_unsuported = True

# HELPER FUNCTIONS COPIED FROM c_ast_to_minic.py
def unsupported(y):
    if y is None:
        print("unsuported called with None")
        return None
    elif y.__class__ == mc.Block:
        print("Ignoring sub block")
        return None
    elif y.__class__ == mc.DeclList:
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
    elif not x:
        return None
    else:
        return transform_ctf(x)
# HELPER FUNCTIONS COPIED FROM c_ast_to_minic.py

def handle_if_statements(orig, optimize_vars=None):


    if_block = orig.iftrue
    else_block = orig.iffalse


    nvs = NodeVisitor()
    nvs.visit(if_block)
    input_args1, output_args1 = get_vars_and_written(nvs)

    if else_block:
        nvs = NodeVisitor()
        nvs.visit(else_block)
        input_args2, output_args2 = get_vars_and_written(nvs)

        in_args = list(set(input_args1 + input_args2))
        out_args = list(set(output_args1 + output_args2))
        else_obj = transform_ctf(orig.iffalse, optimize_vars)

    else:
        in_args = input_args1
        out_args = output_args1
        else_obj = None

    return fast.If(
        transform_ctf(orig.cond),
        transform_ctf(orig.iftrue, optimize_vars),
        else_obj,
        in_args,
        out_args,
    )

def handle_loop_statements(orig):
    block = orig.stmt
    nvs = NodeVisitor()
    nvs.visit(block)

    input_args = []

    init = orig.init

    i = "i"

    if isinstance(init, mc.Assignment):
        i = init.lvalue.name
        input_args.append(str(i))
    elif isinstance(init, mc.DeclList):
        i = init.decls[0].name
        input_args.append(str(i))

    for key in nvs.assignment:
        input_args.append(str(key))

    return fast.LetRec(
        transform_ctf(orig.init),
        input_args,
        transform_ctf(orig.cond),
        transform_ctf(orig.next),
        transform_ctf(orig.stmt),
        coord=orig.coord
    )

def handle_while_statements(orig):
    block = orig.stmt
    nvs = NodeVisitor()
    nvs.visit(block)

    input_args = []
    for key in nvs.assignment:
        input_args.append(str(key))


    return fast.LetRec(
        None,
        input_args,
        transform_ctf(orig.cond),
        None,
        transform_ctf(orig.stmt),
        coord=orig.coord,
    )

def transform_ctf(x, optimize_vars=None):
    """
    Transform function from minic to our function representation
    """
    return {
        # constant ... = 5;
        mc.Constant: (lambda orig: fast.Constant(v(orig.value), coord=orig.coord)),
        # ... = x;
        mc.ID: (lambda orig: fast.ID(v(orig.name))),
        # ... = (left) op (right)
        mc.BinaryOp: (lambda orig: fast.BinaryOp(v(orig.op), transform_ctf(orig.left), transform_ctf(orig.right), coord=orig.coord)),
        # ... = array[...];
        mc.ArrayRef: (lambda orig: fast.ArrayRef(transform_ctf(orig.name), transform_ctf(orig.subscript))),
        # ... = foo(...);
        mc.FuncCall: (lambda orig: fast.FuncCall(transform_ctf(orig.name), tmap(orig.args))),

        #mc.If: (lambda orig: fast.If(transform_ctf(orig.cond), transform_ctf(orig.iftrue), transform_ctf(orig.iffalse))),

        mc.If: (lambda orig: handle_if_statements(orig, optimize_vars)),



        mc.Block: (lambda orig: fast.Block(lmap(transform_ctf, orig.block_items), optimize_vars)),

        # int x = ...
        mc.Decl: (lambda orig: fast.Let(transform_ctf(orig.name), transform_ctf(orig.init), coord=orig.coord)),
        # x = ...
        mc.Assignment: (lambda orig: fast.Let(transform_ctf(orig.lvalue), transform_ctf(orig.rvalue), coord=orig.coord)),
        # int a[] = {1,2,3,...}
        mc.InitList: (lambda orig: fast.ExprList(tmap(orig.exprs))),

        # (...)
        mc.ExprList: (lambda orig: fast.ExprList(tmap(orig.exprs))),

        mc.For: (lambda orig: handle_loop_statements(orig)),
        mc.While: (lambda orig: handle_while_statements(orig)),


        str: (lambda orig: orig),
        int: (lambda orig: orig),
        float: (lambda orig: orig),
        list: (lambda orig: tmap(orig)),
        None: None,
    }.get(x.__class__, lambda y: unsupported(y))(x)


class BlockVisitor(mast.NodeVisitor):

    def __init__(self):
        self.opt_functional_code = []
        self.functional_code = []


    def visit_Block(self, node):
        """
        For each block of code, convert to a functional representation
        ie: every block becomes a function
        """
        new_function = block_converter(node, False)
        self.functional_code.append(str(new_function))

        new_opt_function = block_converter(node, True)
        self.opt_functional_code.append(str(new_function))


def block_converter(block, opt_on):
    """
    Converts minic_ast.Block to func_fast.functionDef
    """

    # clear static vars
    fast.Node.never_used = None
    fast.Node.var_constants = None
    fast.Node.var_constants_reference = {}
    fast.Node.current_opt_index = None

    fast.Node.current_tab_index = None

    # Find all relevant vars for func input and output
    nvs = NodeVisitor()
    nvs.visit(block)
    input_args, output_args = get_vars_and_written(nvs)

    # helpers to optimize code and remove not needed lines
    var_order = nvs.order
    never_used = get_variable_reductions(nvs)
    var_constants = get_variable_constants(nvs)
    optimize_vars = [var_order, never_used, var_constants]

    # remove if statements variables
    never_used, var_constants = remove_if_statements(var_order, never_used, var_constants)


    # update the helper to make the function header
    # currently does not produce correct behabiour
        # 1.
            # int a = q;
            # we dont list q as a required input var from get_vars_and_written()

    # get all declarations, assignments, etc in the block
    block_items = block.block_items

    # transform them to our functional representation
    func_block_items = [transform_ctf(i, optimize_vars) for i in block_items if i]

    #Toggle for optimizer, eventually remove and make it always on

    fast.Node.optimize_vars = opt_on
    fast.Node.never_used = never_used
    fast.Node.var_constants = var_constants
    fast.Node.current_opt_index = 0

    fast.Node.current_tab_index = 1

    func_def = fast.functionDef(input_args, output_args, func_block_items)

    return func_def


# # Testing the code
# # ast = parse_file('./project3inputs/p3_input4')
# ast = parse_file('./project3inputs/p3_input5')
# minic_ast = ctoc.transform(ast)
# vs = BlockVisitor()
# vs.visit(minic_ast)
#
# for function in vs.functional_code:
#     print(function)
#     print("\n")
