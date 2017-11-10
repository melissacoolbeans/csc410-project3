from pycparser import (
    parse_file,
    c_ast
)

import minic.c_ast_to_minic as ctoc
import minic.minic_ast as mast


class NodeVisitor(mast.NodeVisitor):

    def __init__(self):
        self.assignment = {}
        self.other = []
        self.decl = []

    def visit_ID(self, node):
        '''
        For example if statement vars
        '''
        self.other.append(node.name)

    def visit_Decl(self, node):
        """
        a = 5;
        """
        if not isinstance(node.type, mast.FuncDecl):
            self.decl.append(node.name)


    def visit_Assignment(self, assignment):

        lefthand = assignment.lvalue
        righthand = assignment.rvalue
        self.assignment[lefthand.name] = assignment_value_helper(righthand)


class FunctionPrototype:

    def __init__(self, args, output, name):
        self.args = args
        self.output = output
        self.name = name

    def __str__(self):
        str_out = "fun " + self.name + "("


        for i in range(0,len(self.args)):
            str_out += self.args[i]
            if i < len(self.args)-1:
                str_out += ", "

        str_out += ") returns "

        for i in range(0,len(self.output)):
            str_out += self.output[i]
            if i < len(self.output)-1:
                str_out += ", "
        #remove last comma/space

        return str_out


def assignment_value_helper(value, value_map=None):
    '''
    This returns information on right side of assignment
    Returns a map with values:
        Constants
        IDs
        ArrayRef
    '''
    if value_map is None:
        value_map = {
            'Constants': [],
            'IDs': [],
            'ArrayRef': [],
        }

    # constant like 10
    if isinstance(value, mast.Constant):
        value_map['Constants'].append(value.value)

    # var like a
    elif isinstance(value, mast.ID):
        value_map['IDs'].append(value.name)

    # left op right
    elif isinstance(value, mast.BinaryOp):
        left = value.left
        op = value.op
        right = value.right
        #print(left, right)
        # call recursively on the left and right values of the operater
        value_map = assignment_value_helper(left, value_map)
        value_map = assignment_value_helper(right, value_map)

    elif isinstance(value, mast.ArrayRef):
        # array[subscript]
        subscript = value.subscript
        array = value.name

        # call recursively on the array subscript
        value_map = assignment_value_helper(subscript, value_map)

        value_map['ArrayRef'].append(array.name)


    return value_map


def get_vars_and_written(vs):
    '''
    Print all variables in the input and specify which are
    written variables (on the left hand side)
    '''
    variables = []
    written_variables = []

    # add all vars from assignment
    for lefthand in vs.assignment:
        righthand = vs.assignment[lefthand]

        variables.append(lefthand)
        written_variables.append(lefthand)

        # we only want IDs not Constants
        for sub_var in righthand['IDs']:
            variables.append(sub_var)

        for sub_array in righthand['ArrayRef']:
            variables.append(sub_array)

    written_variables += vs.decl
    variables += vs.decl

    # add all other variables (ex if statements, while, etc)
    variables += vs.other

    # variables may be called more than once
    # remove the dups
    variables = list(set(variables))
    written_variables = list(set(written_variables))

    return variables, written_variables

def get_args_and_output(vs):

    variables, written_variables = get_vars_and_written(vs)
    arguments = [x for x in variables if x not in written_variables]
    output = written_variables

    for lefthand in vs.assignment:
        if lefthand in vs.assignment[lefthand]['IDs'][0]:
            arguments.append(lefthand)

    return arguments, written_variables
