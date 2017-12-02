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
        self.decl = {}

        # the order that we see items on the left hand side
        self.order = []

        self.loop = []

    def visit_ID(self, node):
        '''
        For example if statement vars
        '''
        self.order.append(['if', node.name])

        self.other.append(node.name)

    def visit_For(self, node):
        """
        We want to ignore the initilization variables as they should not be Added
        to the optimizer references.
        So just call the visiter on the children.
        """
        NodeVisitor.generic_visit(self, node.stmt)

    def visit_While(self, node):
        NodeVisitor.generic_visit(self, node.stmt)

    def visit_Decl(self, node):
        """
        a = 5;
        we are in a forloop ...
        do not at the init variables to the order ...
        call visit on the child block
        """


        if not isinstance(node.type, mast.FuncDecl):
            lefthand = node.name
            righthand = node.init


            values = assignment_value_helper(node.init)

            if not lefthand in self.decl.keys():
                self.decl[lefthand] = {'Constants': [], 'IDs': [], 'ArrayRef': [], 'count': 0}

            rh_info = assignment_value_helper(righthand)

            self.decl[lefthand]['IDs'].append(rh_info['IDs'])
            self.decl[lefthand]['Constants'].append(rh_info['Constants'])
            self.decl[lefthand]['ArrayRef'].append(rh_info['ArrayRef'])
            self.decl[lefthand]['count'] += 1

            self.order.append([lefthand, rh_info['IDs'] + rh_info['ArrayRef']])

    def visit_Assignment(self, assignment):

        lefthand = assignment.lvalue
        righthand = assignment.rvalue

        if not lefthand.name in self.assignment.keys():
            self.assignment[lefthand.name] = {'Constants': [], 'IDs': [], 'ArrayRef': [], 'count': 0}

        rh_info = assignment_value_helper(righthand)

        self.assignment[lefthand.name]['IDs'].append(rh_info['IDs'])
        self.assignment[lefthand.name]['Constants'].append(rh_info['Constants'])
        self.assignment[lefthand.name]['ArrayRef'].append(rh_info['ArrayRef'])
        self.assignment[lefthand.name]['count'] += 1

        self.order.append([lefthand.name, rh_info['IDs'] + rh_info['ArrayRef']])


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


def get_vars_and_written(vs, remove_dups=True):
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
        for expr in righthand['IDs']:
            for subvar in expr:
                variables.append(subvar)

        for expr in righthand['ArrayRef']:
            for sub_array in expr:
                variables.append(sub_array)
    #TODO: simplyfy to a helper function
    for lefthand in vs.decl:
        righthand = vs.decl[lefthand]

        variables.append(lefthand)
        written_variables.append(lefthand)

        # we only want IDs not Constants
        for expr in righthand['IDs']:
            for subvar in expr:
                variables.append(subvar)

        for expr in righthand['ArrayRef']:
            for sub_array in expr:
                variables.append(sub_array)

    # add all other variables (ex if statements, while, etc)
    variables += vs.other


    if remove_dups:
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


def get_depending_vars(item, vs):

    dependencies = []

    if item in vs.decl:
        righthand = vs.decl[item]
    elif item in vs.assignment:
        righthand = vs.assignment[item]
    else:
        return dependencies

    for expr in righthand['IDs']:
        for subvar in expr:
            dependencies.append(subvar)
    for expr in righthand['ArrayRef']:
        for sub_array in expr:
            dependencies.append(sub_array)

    return dependencies


def get_variable_reductions(vs):


    #TODO: var is overwriten before used, remove old definision

    # initially all vars are available to be reduced
    # this list will contain the index of vars to be pruned
    not_eligable = []

    # 1. To first qualify, a variable must never be used after declared
        # check subsequent declartions and assignments
    index = 0
    for item in vs.order:
        var = item[0]

        if index == len(vs.order) - 1:
            # no more following declarations/assignments
            break
        elif var == 'if':
            not_eligable.append(index)
            index += 1
            continue # we dont support if reductions yet

        for next_item in vs.order[index+1:]:
            next_var = next_item[0]
            next_dependencies = next_item[1]

            if next_dependencies == None:
                continue
            elif next_var == 'if':
                if next_dependencies == var:
                    not_eligable.append(index)
            else:
                for expr in next_dependencies:
                    for subvar in expr:
                        if subvar == var:
                            not_eligable.append(index)
        index += 1


    # 2. check if the variable depends on something that is later reasigned
    index = 0
    for item in vs.order:
        var = item[0]
        dependencies = item[1]

        if index == len(vs.order) - 1:
            # no more following declarations/assignments
            break
        elif var == 'if':
            not_eligable.append(index)
            index += 1
            continue # we dont support if reductions yet

        for next_item in vs.order[index+1:]:
            next_var = next_item[0]
            next_dependencies = next_item[1]

            if next_dependencies == None or next_var == 'if':
                continue # we assume no assignments in a if
            else:
                if next_var in dependencies:
                    not_eligable.append(index)

        index += 1



    eligable = []
    offset = 0

    for index in range(len(vs.order)):
        if index not in not_eligable:
            eligable.append(index)

    return eligable






def get_variable_constants(vs):

    # these vars are defined once as a constant and then used later
    # and never redefined

    eligable = []

    # 1. To first qualify, a variable must never be used after declared
        # check subsequent declartions and assignments
    index = 0
    for item in vs.order:
        var = item[0]
        dependencies = item[1]

        if index == len(vs.order) - 1:
            # no more following declarations/assignments
            break
        elif var == 'if':
            index += 1
            continue # we dont support if reductions yet

        elif dependencies != None and len(dependencies) == 0:
            eligable.append(index)

        index += 1

    return eligable


def remove_if_statements(var_order, never_used, var_constants):
    """
    removes if statements and updates the indexes
    """
    offset = 0
    index = 0

    if_indexes = []

    for item in var_order:
        var = item[0]
        dep = item[1]

        if var == 'if':
            # remove the if
            if len(never_used) and index in never_used:
                never_used.remove(index)
            if len(var_constants) and index in var_constants:
                var_constants.remove(index)

            if_indexes.append(index)
        index += 1

    # update indexes
    for i in range(len(never_used)):
        index = never_used[i]
        offset = len([x for x in if_indexes if x < index])
        never_used[i] -= offset
    for i in range(len(var_constants)):
        index = var_constants[i]
        offset = len([x for x in if_indexes if x < index])
        var_constants[i] -= offset

    return never_used, var_constants



def args_cleaner(args):
    """
    Helper function to format our sets
    """
    string = ""
    first = True
    for arg in args:
        if first or len(args) == 1:
            string += str(arg)
            first = False
        else:
            string += ", %s" % str(arg)
    return string

def optimized_args_cleaner(args, optimizations):
    """
    Helper function to format our sets
    """
    string = ""
    first = True

    optimizations_str = {}
    for i in optimizations:
        optimizations_str[str(i)] = optimizations[i]

    for arg in args:
        if str(arg) in optimizations_str:
            arg_str = optimizations_str[str(arg)]
        else:
            arg_str = str(arg)

        if first or len(args) == 1:
            string += arg_str
            first = False
        else:
            string += ", %s" % arg_str

    return string
