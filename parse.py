import ast

def export_Module(module):
    return '\n'.join(to_source(child) for child in module.body)

def export_Num(num):
    return repr(num.n)

def export_Str(s):
    return repr(s.s)

def export_Bytes(node):
    return repr(node.s)

def export_List(node):
    return '[' + ', '.join(map(to_source, node.elts)) + ']'

def export_Tuple(node):
    return '(' + ', '.join(map(to_source, node.elts)) + ')'

def export_Set(node):
    return '{' + ', '.join(map(to_source, node.elts)) + '}'

def export_Dict(node):
    pairs = []
    for key, value in zip(map(to_source, node.keys), map(to_source, node.values)):
        if key is None:
            pairs.append('**' + value)
        else:
            pairs.append(key + ':' + value)
    return '{' + ', '.join(pairs) + '}'

def export_Ellipsis(node):
    return '...'

def export_NamedConstant(const):
    return repr(const.value)

def export_Name(name):
    return name.id

def export_Starred(node):
    return '*' + to_source(node.value)


priority = {ast.Pow: 13,
            ast.UAdd: 12, ast.USub: 12, ast.Invert: 12,
            ast.Mult: 11, ast.MatMult: 11, ast.Div: 11, ast.FloorDiv: 11, ast.Mod: 11,
            ast.Add: 10, ast.Sub: 10,
            ast.LShift: 9, ast.RShift: 9,
            ast.BitAnd: 8,
            ast.BitXor: 7,
            ast.BitOr: 6,
            ast.In: 5, ast.NotIn: 5, ast.Is: 5, ast.IsNot: 5, ast.Lt: 5, ast.LtE: 5, ast.Gt: 5, ast.GtE: 5,
            ast.NotEq: 5, ast.Eq: 5, ast.Compare: 5,
            ast.Not: 4,
            ast.And: 3,
            ast.Or: 2,
            None: -1}

def export_Expr(node):
    return to_source(node.value)

operator_map = {ast.UAdd: '+',
                ast.USub: '-',
                ast.Not: 'not ',
                ast.Invert: '~',
                ast.Add: '+',
                ast.Sub: '-',
                ast.Mult: '*',
                ast.Div: '/',
                ast.FloorDiv: '//',
                ast.Mod: '%',
                ast.Pow: '**',
                ast.LShift: '<<',
                ast.RShift: '>>',
                ast.BitOr: '|',
                ast.BitXor: '^',
                ast.BitAnd: '&',
                ast.MatMult: '@',
                ast.And: ' and ',
                ast.Or: ' or ',
                ast.Eq: '==',
                ast.NotEq: '!=',
                ast.Lt: '<',
                ast.LtE: '<=',
                ast.Gt: '>',
                ast.GtE: '>=',
                ast.Is: ' is ',
                ast.IsNot: ' is not ',
                ast.In: ' in ',
                ast.NotIn: ' not in '}


def export_UnaryOp(node, parent_op=None, descend=0):
    op = node.op.__class__
    operand = to_source(node.operand, op)
    if parent_op is None:
        parens = False
    elif op is not ast.Not and parent_op == ast.Pow and descend == 1:
        parens = False
    elif priority[parent_op] > priority[op]:
        parens = True
    else:
        parens = False
    s = operator_map[op] + operand
    return '(' + s + ')' if parens else s


def export_BinOp(node, parent_op=None, descend=0):
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


def export_BoolOp(node, parent_op=None, descend=0):
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

def export_Compare(node, parent_op=None, descend=0):
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
    l = ['(']
    if type(left) is str:
        l.append(left)
    else:
        l.extend(left)
    s = left + ''.join(operator_map[cmp.__class__]+value for cmp, value in zip(node.ops, comparators))
    return '(' + s + ')' if parens else s

def export_Call(node):
    norm, key, star, double = [], [], [], []
    try:
        starargs = to_source(node.starargs)
        kwargs = to_source(node.kwargs)
    except Exception:
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

def export_keyword(node):
    if node.arg is None:
        return '**' + to_source(node.value)
    else:
        return node.arg + '=' + to_source(node.value)

def export_IfExp(node):
    body, test, orelse = to_source(node.body), to_source(node.test), to_source(node.orelse)
    return ' '.join([body, 'if', test, 'else', orelse])

def export_Attribute(node):
    value = to_source(node.value)
    return value + '.' + node.attr

def export_Subscript(node):
    value, slice = to_source(node.value), to_source(node.slice)
    return value + '[' + slice + ']'

def export_Index(node):
    return to_source(node.value)

def export_Slice(node):
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

def export_ExtSlice(node):
    dims = map(to_source, node.dims)
    return ', '.join(dims)

def export_ListComp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '[' + ' '.join([elt] + list(generators)) + ']'

def export_SetComp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '{' + ' '.join([elt] + list(generators)) + '}'

def export_GeneratorExp(node):
    elt, generators = to_source(node.elt), map(to_source, node.generators)
    return '(' + ' '.join([elt] + list(generators)) + ')'

def export_DictComp(node):
    key, value, generators = to_source(node.key), to_source(node.value), map(to_source, node.generators)
    return '{' + ' '.join([key + ':' + value] + list(generators)) + '}'

def export_comprehension(node):
    target, iter, ifs = to_source(node.target), to_source(node.iter), list(map(to_source, node.ifs))
    l = []
    if node.is_async:
        l.append('async')
    l.extend(['for', target, 'in', iter])
    if ifs:
        l.append(' '.join(map(lambda s: 'if ' + s, ifs)))
    return ' '.join(l)

def export_Assign(node):
    targets, value = map(to_source, node.targets), to_source(node.value)
    l = []
    for target in targets:
        l.append(target)
        l.append('=')
    l.append(value)
    return ' '.join(l)

def export_AnnAssign(node):
    target, annotation, value = to_source(node.target), to_source(node.annotation), to_source(node.value)
    simple = True if node.simple == 1 else False
    l = [target + ':'] if simple else ['(' + target + '):']
    l.append(annotation)
    if value is not None:
        l.extend(['=', value])
    return ' '.join(l)

def export_AugAssign(node):
    target, value = to_source(node.target), to_source(node.value)
    op = operator_map[node.op.__class__]
    return ' '.join([target, op+'=', value])

def export_Print(node):
    pass  # TODO

def export_Raise(node):
    exc, cause = to_source(node.exc), to_source(node.cause)
    if cause is not None:
        return ' '.join(['raise', exc, 'from', cause])
    else:
        return ' '.join(['raise', exc])

def export_Assert(node):
    test, msg = to_source(node.test), to_source(node.msg)
    if msg is not None:
        return ' '.join(['assert', test+',', msg])
    else:
        return ' '.join(['assert', test])

def export_Delete(node):
    targets = map(to_source, node.targets)
    return 'del ' + ', '.join(targets)

def export_Pass(node):
    return 'pass'

def export_Import(node):
    names = map(to_source, node.names)
    return 'import ' + ', '.join(names)

def export_ImportFrom(node):
    module, names, level = node.module, map(to_source, node.names), node.level
    module = '.'*level + module
    return 'from ' + module + ' import ' + ', '.join(names)

def export_alias(node):
    if node.asname is None:
        return node.name
    else:
        return node.name + ' as ' + node.asname

def export_If(node):
    test = to_source(node.test)
    test = 'if ' + test + ':'
    body_lines = []
    for body_node in node.body:
        body_lines.extend(to_source(body_node).split('\n'))
    body = list(map(lambda x: ' ' * 4 + x, body_lines))
    if node.orelse:
        orelse = node.orelse
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            orelse = orelse[0]
            else_lines = to_source(orelse).split('\n')
            else_lines[0] = 'el' + else_lines[0]
            orelse = else_lines
            return '\n'.join([test] + body + orelse)
        else:
            else_lines = []
            for else_node in orelse:
                else_lines.extend(to_source(else_node).split('\n'))
            orelse = list(map(lambda x: ' '*4 + x, else_lines))
            return '\n'.join([test] + body + ['else:'] + orelse)
    else:
        return '\n'.join([test] + body)

def export_For(node):
    target, iter = to_source(node.target), to_source(node.iter)
    body = list(indent(line_export(node.body)))
    s = 'for ' + target + ' in ' + iter + ':'
    if node.orelse:
        orelse = list(indent(line_export(node.orelse)))
        return '\n'.join([s] + body + ['else:'] + orelse)
    else:
        return '\n'.join([s] + body)

def export_While(node):
    test = to_source(node.test)
    body = list(indent(line_export(node.body)))
    s = 'while ' + test
    if node.orelse:
        orelse = list(indent(line_export(node.orelse)))
        return '\n'.join([s] + body + ['else:'] + orelse)
    else:
        return '\n'.join([s] + body)

def export_Break(node):
    return 'break'

def export_Continue(node):
    return 'continue'

def line_export(nodes):
    return (line for node in nodes for line in to_source(node).split('\n'))

def indent(lines):
    return (' '*4 + line for line in lines)

def export_Try(node):
    l = ['Try:']
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

def export_ExceptHandler(node):
    type, name = to_source(node.type), node.name
    if type is None:
        header = 'except:'
    elif name is None:
        header = 'except ' + type + ':'
    else:
        header = 'except ' + type + ' as ' + name + ':'
    body = list(indent(line_export(node.body)))
    return '\n'.join([header] + body)

def export_With(node):
    items = map(to_source, node.items)
    l = ['with ' + ', '.join(items) + ':']
    l.extend(indent(line_export(node.body)))
    return '\n'.join(l)

def export_withitem(node):
    context_expr, optional_vars = to_source(node.context_expr), to_source(node.optional_vars)
    if optional_vars is None:
        return context_expr
    else:
        return context_expr + ' as ' + optional_vars

def export_FunctionDef(funcdef):
    l = []
    if funcdef.decorator_list:
        l.extend('@' + to_source(decorator) for decorator in funcdef.decorator_list)
    l.append('def ' + funcdef.name + '(' + to_source(funcdef.args) + '):')
    l.extend(indent(line_export(funcdef.body)))
    return '\n'.join(l)

def export_Lambda(node):
    args, body = to_source(node.args), to_source(node.body)
    if args:
        return 'lambda ' + args + ': ' + body
    else:
        return 'lambda: ' + body

def export_arguments(arguments):
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

def export_arg(arg):
    if arg.annotation:
        return ''.join([arg.arg, ': ', to_source(arg.annotation), ''])
    else:
        return arg.arg

def export_Return(node):
    return 'return ' + to_source(node.value)

def export_Yield(node):
    return 'yield ' + to_source(node.value)

def export_YieldFrom(node):
    return 'yield from ' + to_source(node.value)

def export_Global(node):
    return 'global ' + ', '.join(node.names)

def export_Nonlocal(node):
    return 'nonlocal ' + ', '.join(node.names)

def export_ClassDef(node):
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

def export_AsyncFunctionDef(node):
    return 'async ' + export_FunctionDef(node)

def export_Await(node):
    return 'await ' + to_source(node.value)

def export_AsyncFor(node):
    return 'async ' + export_For(node)

def export_AsyncWith(node):
    return 'async ' + export_With(node)

def export_Expression(node):
    return to_source(node.body)

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
    #print('Node:', ast.dump(node) if node is not None else None)
    func = mapping[node.__class__]
    if node.__class__ in [ast.UnaryOp, ast.BinOp, ast.BoolOp, ast.Compare]:
        rtn = func(node, parent_op, descend)
    else:
        rtn = func(node)
    #print(node.__class__, '->', rtn)
    return rtn

def compare_ast(node1, node2):
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


mapping = {type(None): lambda _: None,
           ast.Module: export_Module,
           ast.FunctionDef: export_FunctionDef,
           ast.arguments: export_arguments,
           ast.arg: export_arg,
           ast.Str: export_Str,
           ast.Num: export_Num,
           ast.Name: export_Name,
           ast.Starred: export_Starred,
           ast.NameConstant: export_NamedConstant,
           ast.Pass: export_Pass,
           ast.Expr: export_Expr,
           ast.Bytes: export_Bytes,
           ast.List: export_List,
           ast.Tuple: export_Tuple,
           ast.Set: export_Set,
           ast.Dict: export_Dict,
           ast.Ellipsis: export_Ellipsis,
           ast.UnaryOp: export_UnaryOp,
           ast.BinOp: export_BinOp,
           ast.BoolOp: export_BoolOp,
           ast.Compare: export_Compare,
           ast.Call: export_Call,
           ast.keyword: export_keyword,
           ast.IfExp: export_IfExp,
           ast.Attribute: export_Attribute,
           ast.Subscript: export_Subscript,
           ast.Index: export_Index,
           ast.Slice: export_Slice,
           ast.ExtSlice: export_ExtSlice,
           ast.ListComp: export_ListComp,
           ast.SetComp: export_SetComp,
           ast.GeneratorExp: export_GeneratorExp,
           ast.DictComp: export_DictComp,
           ast.comprehension: export_comprehension,
           ast.Assign: export_Assign,
           ast.AnnAssign: export_AnnAssign,
           ast.AugAssign: export_AugAssign,
           ast.Raise: export_Raise,
           ast.Assert: export_Assert,
           ast.Delete: export_Delete,
           ast.Import: export_Import,
           ast.ImportFrom: export_ImportFrom,
           ast.alias: export_alias,
           ast.If: export_If,
           ast.For: export_For,
           ast.While: export_While,
           ast.Break: export_Break,
           ast.Continue: export_Continue,
           ast.Try: export_Try,
           ast.ExceptHandler: export_ExceptHandler,
           ast.With: export_With,
           ast.withitem: export_withitem,
           ast.Lambda: export_Lambda,
           ast.Return: export_Return,
           ast.Yield: export_Yield,
           ast.YieldFrom: export_YieldFrom,
           ast.Global: export_Global,
           ast.Nonlocal: export_Nonlocal,
           ast.ClassDef: export_ClassDef,
           ast.AsyncFunctionDef: export_AsyncFunctionDef,
           ast.Await: export_Await,
           ast.AsyncFor: export_AsyncFor,
           ast.AsyncWith: export_AsyncWith,
           ast.Expression: export_Expression}

if __name__ == '__main__':
    tree = ast.parse(open('test.py', 'r').read(), 'test.py', 'exec')
    print(tree._fields)
    for node in ast.walk(tree):
        node.children = []
        for child in ast.iter_child_nodes(node):
            child.parent = node
            node.children.append(child)
    s = to_source(tree)
    print('Max depth: %s' % max_depth)
    print(repr(s))