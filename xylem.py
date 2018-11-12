# Xylem: Convert Python Abstract Syntax Trees (ASTs) to source code.
# Copyright (C) 2018 Ariel Antonitis. Licensed under the MIT license.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# xylem.py
""" Xylem v0.9.0

Convert Python Abstract Syntax Trees (ASTs) to source code.

Copyright (C) 2018 Ariel Antonitis. Licensed under the MIT License.
"""
import ast


__version__ = '0.9.1'
url = 'https://github.com/arantonitis/xylem'


def _src_Module(node):
    return '\n'.join(to_source(child) for child in node.body)


def _src_Num(node):
    return repr(node.n)


def _src_Str(node):
    return repr(node.s)


def _src_Bytes(node):
    return repr(node.s)


def _src_JoinedStr(node, raw=False):
    f_string = ''.join(_src_FormattedValue(value, raw=True) if isinstance(value, ast.FormattedValue) else value.s
                       for value in node.values)
    if raw:
        return f_string
    else:
        return 'f' + repr(f_string)


def _src_FormattedValue(node, raw=False):
    value = to_source(node.value)
    l = [value]
    if node.format_spec is not None:
        l.append(':')
        l.append(_src_JoinedStr(node.format_spec, raw=True))
    if node.conversion != -1:
        l.append('!' + chr(node.conversion))
    if raw:
        return '{' + ''.join(l) + '}'
    else:
        return 'f' + repr('{' + ''.join(l) + '}')


def _src_List(node):
    return '[' + ', '.join(to_source(e) for e in node.elts) + ']'


def _src_Tuple(node):
    return '(' + ', '.join(to_source(e) for e in node.elts) + ')'


def _src_Set(node):
    return '{' + ', '.join(to_source(e) for e in node.elts) + '}'


def _src_Dict(node):
    # Create a generator consisting of all key=value and **value pairs in the node, then join them
    return '{' + ', '.join('**' + value if key is None else key + ':' + value
                           for key, value in zip(map(to_source, node.keys), map(to_source, node.values))) + '}'


def _src_Ellipsis(node):
    return '...'


def _src_NameConstant(const):
    return repr(const.value)


def _src_Name(name):
    return name.id


def _src_Starred(node):
    return '*' + to_source(node.value)


# Mapping from AST operators to their priority/precedence. Higher numbers represent higher precedence.
priority = {ast.Pow: 13, ast.UAdd: 12, ast.USub: 12, ast.Invert: 12, ast.Mult: 11, ast.MatMult: 11, ast.Div: 11,
            ast.FloorDiv: 11, ast.Mod: 11, ast.Add: 10, ast.Sub: 10, ast.LShift: 9, ast.RShift: 9, ast.BitAnd: 8,
            ast.BitXor: 7, ast.BitOr: 6, ast.In: 5, ast.NotIn: 5, ast.Is: 5, ast.IsNot: 5, ast.Lt: 5, ast.LtE: 5,
            ast.Gt: 5, ast.GtE: 5, ast.NotEq: 5, ast.Eq: 5, ast.Compare: 5, ast.Not: 4, ast.And: 3, ast.Or: 2, None: -1}

# Mapping from AST operators to the string representing that operator
operator_map = {ast.UAdd: '+', ast.USub: '-', ast.Not: 'not ', ast.Invert: '~', ast.Add: '+', ast.Sub: '-',
                ast.Mult: '*', ast.Div: '/', ast.FloorDiv: '//', ast.Mod: '%', ast.Pow: '**', ast.LShift: '<<',
                ast.RShift: '>>', ast.BitOr: '|', ast.BitXor: '^', ast.BitAnd: '&', ast.MatMult: '@', ast.And: ' and ',
                ast.Or: ' or ', ast.Eq: '==', ast.NotEq: '!=', ast.Lt: '<', ast.LtE: '<=', ast.Gt: '>', ast.GtE: '>=',
                ast.Is: ' is ', ast.IsNot: ' is not ', ast.In: ' in ', ast.NotIn: ' not in '}


def _src_Expr(node):
    return to_source(node.value)


def _src_UnaryOp(node, parent_op=None, descend=0):
    op = node.op.__class__
    operand = to_source(node.operand, op)
    if parent_op is None:
        parens = False
    elif op is not ast.Not and parent_op == ast.Pow and descend == 1:  # Parens not needed on the right side of 2**-1
        parens = False
    elif priority[parent_op] > priority[op]:
        parens = True
    else:
        parens = False
    s = operator_map[op] + operand
    return '(' + s + ')' if parens else s


def _src_BinOp(node, parent_op=None, descend=0):
    op = node.op.__class__
    left, right = to_source(node.left, op, -1), to_source(node.right, op, 1)
    if parent_op is None:
        parens = False
    elif priority[parent_op] > priority[op]:
        parens = True
    elif op == ast.Sub == parent_op and descend == 1:
        parens = True
    elif op in [ast.Div, ast.FloorDiv, ast.Mod] and parent_op in [ast.Div, ast.FloorDiv, ast.Mod] and descend == 1:
        parens = True
    elif op in [ast.LShift, ast.RShift] and parent_op in [ast.LShift, ast.RShift] and descend == 1:
        parens = True
    else:
        parens = False
    s = ''.join([left, operator_map[node.op.__class__], right])
    return '(' + s + ')' if parens else s


def _src_BoolOp(node, parent_op=None, descend=0):
    op = node.op.__class__
    values = map(lambda s: to_source(s, op), node.values)
    if parent_op is None:
        parens = False
    elif priority[parent_op] > priority[op]:
        parens = True
    else:
        parens = False
    s = operator_map[op].join(values)
    return '(' + s + ')' if parens else s


def _src_Compare(node, parent_op=None, descend=0):
    op = node.__class__
    comparators = map(lambda s: to_source(s, op), node.comparators)
    left = to_source(node.left, op)
    if parent_op is None:
        parens = False
    elif priority[parent_op] > priority[op]:
        parens = True
    elif op == ast.Compare == parent_op:
        parens = True
    else:
        parens = False
    s = left + ''.join(operator_map[cmp.__class__]+value for cmp, value in zip(node.ops, comparators))
    return '(' + s + ')' if parens else s


def _src_Call(node):
    norm, key, star, double = [], [], [], []
    try:
        starargs, kwargs = to_source(node.starargs), to_source(node.kwargs)
    except AttributeError:  # starargs and kwargs were removed in Python 3.5
        for arg in node.args + node.keywords:
            exported = to_source(arg)
            if isinstance(arg, ast.Starred):
                star.append(exported)
            elif isinstance(arg, ast.keyword):
                if arg.arg is None:
                    double.append(exported)
                else:
                    key.append(exported)
            else:
                norm.append(exported)
    else:
        norm = list(map(to_source, node.args))
        key = list(map(to_source, node.keywords))
        star = ['*' + starargs] if starargs else []
        double = ['**' + kwargs] if kwargs else []
    finally:
        return to_source(node.func) + '(' + ', '.join(norm + key + star + double) + ')'


def _src_keyword(node):
    if node.arg is None:
        return '**' + to_source(node.value)
    else:
        return node.arg + '=' + to_source(node.value)


def _src_IfExp(node):
    body, test, orelse = to_source(node.body), to_source(node.test), to_source(node.orelse)
    return ' '.join([body, 'if', test, 'else', orelse])


def _src_Attribute(node):
    value = to_source(node.value)
    return value + '.' + node.attr


def _src_Subscript(node):
    value, slice = to_source(node.value), to_source(node.slice)
    return value + '[' + slice + ']'


def _src_Index(node):
    return to_source(node.value)


def _src_Slice(node):
    lower, upper, step = to_source(node.lower), to_source(node.upper), to_source(node.step)
    if step is None:
        if upper is None and lower is None:
            return ':'
        elif upper is None:
            return lower + ':'
        elif lower is None:
            return ':' + upper
        else:
            return lower + ':' + upper
    else:
        if upper is None and lower is None:
            return '::' + step
        elif upper is None:
            return lower + '::' + step
        elif lower is None:
            return ':' + upper + ':' + step
        else:
            return lower + ':' + upper + ':' + step


def _src_ExtSlice(node):
    dims = map(to_source, node.dims)
    return ', '.join(dims)


def _src_ListComp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '[' + ' '.join([elt] + list(generators)) + ']'


def _src_SetComp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '{' + ' '.join([elt] + list(generators)) + '}'


def _src_GeneratorExp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '(' + ' '.join([elt] + list(generators)) + ')'


def _src_DictComp(node):
    key, value, generators = to_source(node.key), to_source(node.value), map(to_source, node.generators)
    return '{' + ' '.join([key + ':' + value] + list(generators)) + '}'


def _src_comprehension(node):
    target, iter, ifs = to_source(node.target), to_source(node.iter), list(map(to_source, node.ifs))
    l = []
    if node.is_async:
        l.append('async')
    l.extend(['for', target, 'in', iter])
    if ifs:
        l.append(' '.join(map(lambda s: 'if ' + s, ifs)))
    return ' '.join(l)


def _src_Assign(node):
    targets, value = map(to_source, node.targets), to_source(node.value)
    return ' = '.join(targets) + ' = ' + value


def _src_AnnAssign(node):
    target, annotation, value = to_source(node.target), to_source(node.annotation), to_source(node.value)
    l = [target + ':'] if node.simple == 1 else ['(' + target + '):']
    l.append(annotation)
    if value is not None:
        l.extend(['=', value])
    return ' '.join(l)


def _src_AugAssign(node):
    target, value = to_source(node.target), to_source(node.value)
    return ' '.join([target, operator_map[node.op.__class__]+'=', value])


def _src_Print(node):  # TODO Python 2 only
    return 'print ' + ', '.join(node.values) + '>>%s' % node.dest if node.dest else '' + ',' if node.nl else ''


def _src_Raise(node):
    exc, cause = to_source(node.exc), to_source(node.cause)
    if exc is None:
        return 'raise'
    elif cause is not None:
        return ' '.join(['raise', exc, 'from', cause])
    else:
        return ' '.join(['raise', exc])


def _src_Assert(node):
    test, msg = to_source(node.test), to_source(node.msg)
    if msg is not None:
        return ' '.join(['assert', test+', ', msg])
    else:
        return ' '.join(['assert', test])


def _src_Delete(node):
    return 'del ' + ', '.join(to_source(target) for target in node.targets)


def _src_Pass(node):
    return 'pass'


def _src_Import(node):
    return 'import ' + ', '.join(to_source(name) for name in node.names)


def _src_ImportFrom(node):
    module, names, level = node.module, map(to_source, node.names), node.level
    module = '.'*level + (module if module else '')
    return 'from ' + module + ' import ' + ', '.join(names)


def _src_alias(node):
    return node.name if node.asname is None else node.name + ' as ' + node.asname


def _src_If(node):
    test = 'if ' + to_source(node.test) + ':'
    body = list(indent(line_export(node.body)))
    if node.orelse:
        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            orelse = node.orelse[0]
            else_lines = to_source(orelse).split('\n')
            else_lines[0] = 'el' + else_lines[0]
            orelse = else_lines
            return '\n'.join([test] + body + orelse)
        else:
            else_lines = []
            for else_node in node.orelse:
                else_lines.extend(to_source(else_node).split('\n'))
            orelse = list(map(lambda x: ' '*4 + x, else_lines))
            return '\n'.join([test] + body + ['else:'] + orelse)
    else:
        return '\n'.join([test] + body)


def _src_For(node):
    target, iter = to_source(node.target), to_source(node.iter)
    body = list(indent(line_export(node.body)))
    s = 'for ' + target + ' in ' + iter + ':'
    if node.orelse:
        orelse = list(indent(line_export(node.orelse)))
        return '\n'.join([s] + body + ['else:'] + orelse)
    else:
        return '\n'.join([s] + body)


def _src_While(node):
    test = to_source(node.test)
    body = list(indent(line_export(node.body)))
    s = 'while ' + test + ':'
    if node.orelse:
        orelse = list(indent(line_export(node.orelse)))
        return '\n'.join([s] + body + ['else:'] + orelse)
    else:
        return '\n'.join([s] + body)


def _src_Break(node):
    return 'break'


def _src_Continue(node):
    return 'continue'


def line_export(nodes):
    return (line for node in nodes for line in to_source(node).split('\n'))


def indent(lines):
    return (' '*4 + line for line in lines)


def _src_Try(node):
    l = ['try:']
    l.extend(indent(line_export(node.body)))
    if node.handlers:
        l.extend(line_export(node.handlers))
    if node.orelse:
        l.append('else:')
        l.extend(indent(line_export(node.orelse)))
    if node.finalbody:
        l.append('finally:')
        l.extend(indent(line_export(node.finalbody)))
    return '\n'.join(l)


def _src_ExceptHandler(node):
    type, name = to_source(node.type), node.name
    if type is None:
        header = 'except:'
    elif name is None:
        header = 'except ' + type + ':'
    else:
        header = 'except ' + type + ' as ' + name + ':'
    body = list(indent(line_export(node.body)))
    return '\n'.join([header] + body)


def _src_With(node):
    l = ['with ' + ', '.join(to_source(item) for item in node.items) + ':']
    l.extend(indent(line_export(node.body)))
    return '\n'.join(l)


def _src_withitem(node):
    context_expr, optional_vars = to_source(node.context_expr), to_source(node.optional_vars)
    if optional_vars is None:
        return context_expr
    else:
        return context_expr + ' as ' + optional_vars


def _src_FunctionDef(funcdef):  # TODO: Lots of compatibility before Python 3, 3.3
    l = []
    if funcdef.decorator_list:
        l.extend('@' + to_source(decorator) for decorator in funcdef.decorator_list)
    return_annotation = ' -> ' + to_source(funcdef.returns) if funcdef.returns else ''
    l.append('def ' + funcdef.name + '(' + to_source(funcdef.args) + ')' + return_annotation + ':')
    l.extend(indent(line_export(funcdef.body)))
    return '\n'.join(l)


def _src_Lambda(node):
    args, body = to_source(node.args), to_source(node.body)
    if args:
        return 'lambda ' + args + ': ' + body
    else:
        return 'lambda: ' + body


def _src_arguments(arguments):
    args = list(map(to_source, arguments.args))
    kwonly = list(map(to_source, arguments.kwonlyargs))
    vararg, kwarg = to_source(arguments.vararg), to_source(arguments.kwarg)
    defaults = list(map(to_source, arguments.defaults))
    kw_defaults = list(map(to_source, arguments.kw_defaults))
    defaults = [None]*(len(args)-len(defaults)) + defaults
    l = [arg + '=' + default if default is not None else arg for arg, default in zip(args, defaults)]
    if vararg is not None:
        l.append('*' + vararg)
    l += [arg + '=' + default if default is not None else arg for arg, default in zip(kwonly, kw_defaults)]
    if kwarg:
        l.append('**' + kwarg)
    return ', '.join(l)


def _src_arg(arg):
    if arg.annotation:
        return ''.join([arg.arg, ': ', to_source(arg.annotation), ''])
    else:
        return arg.arg


def _src_Return(node):
    return 'return ' + to_source(node.value) if node.value else 'return'


def _src_Yield(node):
    return 'yield ' + to_source(node.value)


def _src_YieldFrom(node):
    return 'yield from ' + to_source(node.value)


def _src_Global(node):
    return 'global ' + ', '.join(node.names)


def _src_Nonlocal(node):
    return 'nonlocal ' + ', '.join(node.names)


def _src_ClassDef(node):
    l = []
    if node.decorator_list:
        l.extend('@' + to_source(decorator) for decorator in node.decorator_list)
    args = []
    if node.bases:
        args.extend(to_source(base) for base in node.bases)
    if node.keywords:
        args.extend(to_source(keyword) for keyword in node.keywords)
    if node.bases or node.keywords:
        l.append('class ' + node.name + '(' + ', '.join(args) + '):')
    else:
        l.append('class ' + node.name + ':')
    l.extend(indent(line_export(node.body)))
    return '\n'.join(l)


def _src_AsyncFunctionDef(node):
    return 'async ' + _src_FunctionDef(node)


def _src_Await(node):
    return 'await ' + to_source(node.value)


def _src_AsyncFor(node):
    return 'async ' + _src_For(node)


def _src_AsyncWith(node):
    return 'async ' + _src_With(node)


def _src_Expression(node):
    return to_source(node.body)

# Maps AST classes to the functions used to turn them into source
mapping = {getattr(ast, name[5:]): obj for name, obj in globals().copy().items()
           if name.startswith('_src_') and callable(obj) and hasattr(ast, name[5:])}


max_depth = 0
def depth_counter(f):
    depth = 0
    def wrapper(*args, **kwargs):
        global max_depth
        nonlocal depth
        depth += 1
        if depth > max_depth:
            max_depth = depth
        rtn = f(*args, **kwargs)
        depth -= 1
        return rtn
    return wrapper


@depth_counter
def to_source(node, parent_op=None, descend=0):
    """ Converts an AST node into source code.

    Args:
        node: Any AST node derived from ast.AST.

    Returns: str: A string containing the source code corresponding to the AST.
    """
    if node is None:
        return None
    func = mapping[node.__class__]
    if func in (_src_UnaryOp, _src_BinOp, _src_BoolOp, _src_Compare):
        rtn = func(node, parent_op, descend)
    else:
        rtn = func(node)
    return rtn


def compare_ast(node1, node2):
    """ Compare two ASTS to determine if they are the same.

    Args:
        node1: The first node.
        node2: The second node.

    Returns: bool: True if the nodes represent the same AST, false otherwise.
    """
    if type(node1) is not type(node2):
        return False
    if isinstance(node1, ast.AST):
        for field, child in ast.iter_fields(node1):
            if field in ['lineno', 'col_offset', 'ctx']:
                continue
            if not compare_ast(child, getattr(node2, field)):
                return False
        return True
    elif isinstance(node1, list):
        return all(compare_ast(e1, e2) for e1, e2 in zip(node1, node2))
    else:
        return node1 == node2

__all__ = ['to_source', 'compare_ast']
