#-----------------------------------------------------------------
#
# Functional AST Node classes.
#
# Most of the code is copied from minic_ast.py
# credits to:
# Eli Bendersky [http://eli.thegreenplace.net]
# Victor Nicolet
# License: BSD
#
#
# Major Changes:
# 1. Added a Let Operater
#    Removed Assignment as they can be represented as Let
#
# 2. Added a LetRec Operater
#    Removed DoWhile, ForDone, While as they can be represented as a LetRec
#
# 3. Removed: ArrayDecl, ArrayRef
#    As they can be represented with ExprList
#
# 4. Returning tuples can also be represented as ExprList
#-----------------------------------------------------------------

import sys


class Node(object):
    __slots__ = ()
    """ Abstract base class for AST nodes.
    """
    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and
            children (recursively) to a buffer.

            buf:
                Open IO buffer into which the Node is printed.

            offset:
                Initial offset (amount of leading spaces)

            attrnames:
                True if you want to see the attribute names in
                name=value pairs. False to only see the values.

            nodenames:
                True if you want to see the actual node names
                within their parents.

            showcoord:
                Do you want the coordinates of each Node to be
                displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self,n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            buf.write(' (at %s)' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(
                buf,
                offset=offset + 2,
                attrnames=attrnames,
                nodenames=nodenames,
                showcoord=showcoord,
                _my_node_name=child_name)


class NodeVisitor(object):
    """ A base NodeVisitor class for visiting c_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the bant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """
    def visit(self, node):
        """ Visit a node.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c_name, c in node.children():
            self.visit(c)

class Let(Node):
    __slots__ = ('lvalue', 'rvalue', 'in_statement', 'coord', '__weakref__')

    def __init__(self, lvalue, rvalue, in_statement=None, coord=None):
        self.lvalue = lvalue # the input vars on the left side of =
        self.rvalue = rvalue # the expression on the right side of the =
        self.in_statement = in_statement # the value after the in statement in a let
        self.coord = coord

    def children(self):
		nodelist = []
		if self.function_name is not None: nodelist.append(("function_name", self.function_name))
		if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
		if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
		if self.in_statement is not None: nodelist.append(("in_statement", self.in_statement))
		return tuple(nodelist)

    def __str__(self):
        return "let %s = %s" % (self.lvalue, self.rvalue.__str__())

class Constant(Node):
    __slots__ = ('value', 'coord', '__weakref__')

    def __init__(self, value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __str__(self):
        return "%s" % self.value

    attr_names = ('value', )

class LetRec(Node):
    __slots__ = (
		'function_name',
		'lvalue',
		'if_statement',
		'if_then',
		'else_then'
		'in_statement',
		'coord',
		'__weakref__'
	)

    def __init__(
		self,
		function_name,
		lvalue,
		if_statement,
		if_then,
		else_then,
		in_statement,
		coord=None
	):
		self.function_name = function_name
		self.lvalue = lvalue  # the input vars on the left side of =
		self.if_statement = if_statement # expression on the if condition
		self.if_then = if_then # expression to execute if the if condition passes
		self.else_then = else_then # expression to execute if the if condition fails
		self.in_statement = in_statement # the value after the in statement in a let
		self.coord = coord

    def children(self):
		nodelist = []
		if self.function_name is not None: nodelist.append(("function_name", self.function_name))
		if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
		if self.if_statement is not None: nodelist.append(("if_statement", self.if_statement))
		if self.if_then is not None: nodelist.append(("if_then", self.if_then))
		if self.else_then is not None: nodelist.append(("else_then", self.else_then))
		if self.in_statement is not None: nodelist.append(("in_statement", self.in_statement))
		return tuple(nodelist)


class BinaryOp(Node):
    __slots__ = ('op', 'left', 'right', 'coord', '__weakref__')

    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None: nodelist.append(("left", self.left))
        if self.right is not None: nodelist.append(("right", self.right))
        return tuple(nodelist)

    def __str__(self):
        return "%s %s %s" % (self.left, self.op, self.right)

    attr_names = ('op', )


#TODO: remove
class Block(Node):
    __slots__ = ('block_items', 'coord', '__weakref__')

    def __init__(self, block_items, coord=None):
        self.block_items = block_items
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.block_items or []):
            nodelist.append(("block_items[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class functionDef(Node):
    __slots__ = ('input_args', 'output_args', 'block_items', 'coord', '__weakref__')
    #TODO: ADD A FUNCTION NAME INPUT
    def __init__(self, input_args, output_args, block_items, coord=None):
        self.input_args = input_args
        self.output_args = output_args
        self.block_items = block_items
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.block_items or []):
            nodelist.append(("block_items[%d]" % i, child))
        return tuple(nodelist)


    def __str__(self):
        """
        Our AST in Functional code format
        """
        def args_cleaner(args):
            """
            Helper function to format our sets
            """
            string = ""
            first = True
            for arg in args:
                if first:
                    string += str(arg)
                    first = False
                else:
                    string += ", %s" % str(arg)
            return string

        # function name, inputs, outputs
        string = "fun block_function(%s) returns (%s) =\n" % (
            args_cleaner(self.input_args),
            args_cleaner(self.output_args)
        )

        # now go over all our body items
        tabs = 1
        for body in self.block_items:
            string += tabs * "\t"
            # print body
            # body can be a let or let rec
            string += "%s in \n" % body.__str__()
            #indent
            tabs += 1

        # add final return
        string += tabs * "\t"
        string += "(%s)" % args_cleaner(self.output_args)

        # return the string
        return string

    attr_names = ()


class Decl(Node):
    __slots__ = ('name', 'funcspec', 'init', 'coord', '__weakref__')

    def __init__(self, name, funcspec, init, coord=None):
        self.name = name
        self.funcspec = funcspec
        self.init = init
        self.coord = coord

    def children(self):
        nodelist = []
        if self.init is not None: nodelist.append(("init", self.init))
        return tuple(nodelist)

    def __str__(self):
        return "%s = %s" % (self.name, self.init.__str__())

    attr_names = ('name', 'funcspec', )


class DeclList(Node):
    __slots__ = ('decls', 'coord', '__weakref__')

    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(("decls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()



class EmptyStatement(Node):
    __slots__ = ('coord', '__weakref__')
    def __init__(self, coord=None):
        self.coord = coord

    def children(self):
        return ()

    attr_names = ()


class ExprList(Node):
	'''
	Lists can also represent:
	- arrays
	- tuples
	'''
	__slots__ = ('exprs', 'coord', '__weakref__')

	def __init__(self, exprs, coord=None):
		self.exprs = exprs
		self.coord = coord

	def children(self):
		nodelist = []
		for i, child in enumerate(self.exprs or []):
			nodelist.append(("exprs[%d]" % i, child))
		return tuple(nodelist)

	attr_names = ()


class FileAST(Node):
    __slots__ = ('ext', 'coord', '__weakref__')

    def __init__(self, ext, coord=None):
        self.ext = ext
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.ext or []):
            nodelist.append(("ext[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord', '__weakref__')

    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))
        if self.args is not None: nodelist.append(("args", self.args))
        return tuple(nodelist)

    attr_names = ()


class FuncDecl(Node):
    __slots__ = ('args', 'type', 'coord', '__weakref__')

    def __init__(self, args, type, coord=None):
        self.args = args
        self.type = type
        self.coord = coord

    def children(self):
        nodelist = []
        if self.args is not None: nodelist.append(("args", self.args))
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)

    attr_names = ()


class FuncDef(Node):
    #todo update
    __slots__ = ('decl', 'param_decls', 'body', 'coord', '__weakref__')

    def __init__(self, decl, param_decls, body, coord=None):
        self.decl = decl
        self.param_decls = param_decls
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.decl is not None: nodelist.append(("decl", self.decl))
        if self.body is not None: nodelist.append(("body", self.body))
        for i, child in enumerate(self.param_decls or []):
            nodelist.append(("param_decls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class ID(Node):
    __slots__ = ('name', 'coord', '__weakref__')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __str__(self):
        return self.name

    attr_names = ('name', )


class IdentifierType(Node):
    __slots__ = ('names', 'coord', '__weakref__')
    def __init__(self, names, coord=None):
        self.names = names
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('names', )


class If(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'coord', '__weakref__')
    def __init__(self, cond, iftrue, iffalse, coord=None):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.iftrue is not None: nodelist.append(("iftrue", self.iftrue))
        if self.iffalse is not None: nodelist.append(("iffalse", self.iffalse))
        return tuple(nodelist)

    attr_names = ()


class InitList(Node):
    __slots__ = ('exprs', 'coord', '__weakref__')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class Label(Node):
    __slots__ = ('name', 'stmt', 'coord', '__weakref__')

    def __init__(self, name, stmt, coord=None):
        self.name = name
        self.stmt = stmt
        self.coord = coord

    def children(self):
        nodelist = []
        if self.stmt is not None: nodelist.append(("stmt", self.stmt))
        return tuple(nodelist)

    attr_names = ('name', )


class NamedInitializer(Node):
    __slots__ = ('name', 'expr', 'coord', '__weakref__')

    def __init__(self, name, expr, coord=None):
        self.name = name
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(("expr", self.expr))
        for i, child in enumerate(self.name or []):
            nodelist.append(("name[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class ParamList(Node):
    __slots__ = ('params', 'coord', '__weakref__')

    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(("params[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()


class PtrDecl(Node):
    __slots__ = ('type', 'coord', '__weakref__')

    def __init__(self, ptrtype, coord=None):
        self.type = ptrtype
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)

    attr_names = ('quals', )


class Return(Node):
    __slots__ = ('expr', 'coord', '__weakref__')

    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(("expr", self.expr))
        return tuple(nodelist)

    attr_names = ()


class TernaryOp(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'coord', '__weakref__')

    def __init__(self, cond, iftrue, iffalse, coord=None):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.iftrue is not None: nodelist.append(("iftrue", self.iftrue))
        if self.iffalse is not None: nodelist.append(("iffalse", self.iffalse))
        return tuple(nodelist)

    attr_names = ()


class Typename(Node):
    __slots__ = ('name', 'type', 'coord', '__weakref__')

    def __init__(self, name, ttype, coord=None):
        self.name = name
        self.type = ttype
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)

    attr_names = ('name', )


class TypeDecl(Node):
    __slots__ = ('declname', 'type', 'coord', '__weakref__')

    def __init__(self, declname, ttype, coord=None):
        self.declname = declname
        self.type = ttype
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        return tuple(nodelist)

    attr_names = ('name', )


class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'coord', '__weakref__')

    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(("expr", self.expr))
        return tuple(nodelist)

    attr_names = ('op', )


class Union(Node):
    __slots__ = ('name', 'decls', 'coord', '__weakref__')

    def __init__(self, name, decls, coord=None):
        self.name = name
        self.decls = decls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(("decls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ('name', )


# class ArrayDecl(Node):
#     __slots__ = ('type', 'dim', 'dim_quals', 'coord', '__weakref__')
# class ArrayRef(Node):
#     __slots__ = ('name', 'subscript', 'coord', '__weakref__')
# class Assignment(Node):
#     __slots__ = ('op', 'lvalue', 'rvalue', 'coord', '__weakref__')
# class BinaryOp(Node):
#     __slots__ = ('op', 'left', 'right', 'coord', '__weakref__')
# class Break(Node):
#     __slots__ = ('coord', '__weakref__')
# class Case(Node):
#     __slots__ = ('expr', 'stmts', 'coord', '__weakref__')
# class Cast(Node):
#     __slots__ = ('to_type', 'expr', 'coord', '__weakref__')
# class Compound(Node):
#     __slots__ = ('block_items', 'coord', '__weakref__')
# class CompoundLiteral(Node):
#     __slots__ = ('type', 'init', 'coord', '__weakref__')
# class Constant(Node):
#     __slots__ = ('type', 'value', 'coord', '__weakref__')
# class Continue(Node):
#     __slots__ = ('coord', '__weakref__')
# class Decl(Node):
#     __slots__ = ('name', 'quals', 'storage', 'funcspec', 'type', 'init', 'bitsize', 'coord', '__weakref__')
# class DeclList(Node):
#     __slots__ = ('decls', 'coord', '__weakref__')
# class Default(Node):
#     __slots__ = ('stmts', 'coord', '__weakref__')
# class DoWhile(Node):
#     __slots__ = ('cond', 'stmt', 'coord', '__weakref__')
# class EllipsisParam(Node):
#     __slots__ = ('coord', '__weakref__')
# class EmptyStatement(Node):
#     __slots__ = ('coord', '__weakref__')
# class Enum(Node):
#     __slots__ = ('name', 'values', 'coord', '__weakref__')
# class Enumerator(Node):
#     __slots__ = ('name', 'value', 'coord', '__weakref__')
# class EnumeratorList(Node):
#     __slots__ = ('enumerators', 'coord', '__weakref__')
# class ExprList(Node):
#     __slots__ = ('exprs', 'coord', '__weakref__')
# class FileAST(Node):
#     __slots__ = ('ext', 'coord', '__weakref__')
# class For(Node):
#     __slots__ = ('init', 'cond', 'next', 'stmt', 'coord', '__weakref__')
# class FuncCall(Node):
#     __slots__ = ('name', 'args', 'coord', '__weakref__')
# class FuncDecl(Node):
#     __slots__ = ('args', 'type', 'coord', '__weakref__')
# class FuncDef(Node):
#     __slots__ = ('decl', 'param_decls', 'body', 'coord', '__weakref__')
# class Goto(Node):
#     __slots__ = ('name', 'coord', '__weakref__')
# class ID(Node):
#     __slots__ = ('name', 'coord', '__weakref__')
# class IdentifierType(Node):
#     __slots__ = ('names', 'coord', '__weakref__')
# class If(Node):
#     __slots__ = ('cond', 'iftrue', 'iffalse', 'coord', '__weakref__')
# class InitList(Node):
#     __slots__ = ('exprs', 'coord', '__weakref__')
# class Label(Node):
#     __slots__ = ('name', 'stmt', 'coord', '__weakref__')
# class NamedInitializer(Node):
#     __slots__ = ('name', 'expr', 'coord', '__weakref__')
# class ParamList(Node):
#     __slots__ = ('params', 'coord', '__weakref__')
# class PtrDecl(Node):
#     __slots__ = ('quals', 'type', 'coord', '__weakref__')
# class Return(Node):
#     __slots__ = ('expr', 'coord', '__weakref__')
# class Struct(Node):
#     __slots__ = ('name', 'decls', 'coord', '__weakref__')
# class StructRef(Node):
#     __slots__ = ('name', 'type', 'field', 'coord', '__weakref__')
# class Switch(Node):
#     __slots__ = ('cond', 'stmt', 'coord', '__weakref__')
# class TernaryOp(Node):
#     __slots__ = ('cond', 'iftrue', 'iffalse', 'coord', '__weakref__')
# class TypeDecl(Node):
#     __slots__ = ('declname', 'quals', 'type', 'coord', '__weakref__')
# class Typedef(Node):
#     __slots__ = ('name', 'quals', 'storage', 'type', 'coord', '__weakref__')
# class Typename(Node):
#     __slots__ = ('name', 'quals', 'type', 'coord', '__weakref__')
# class UnaryOp(Node):
#     __slots__ = ('op', 'expr', 'coord', '__weakref__')
# class Union(Node):
#     __slots__ = ('name', 'decls', 'coord', '__weakref__')
# class While(Node):
#     __slots__ = ('cond', 'stmt', 'coord', '__weakref__')
# class Pragma(Node):
#     __slots__ = ('string', 'coord', '__weakref__')
