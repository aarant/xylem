import ast

class AccessWrapper(ast.NodeTransformer):
    def __init__(self, func_name):
        self.func_name = func_name

    def wrap_node(self, node):
        return ast.Call(func=ast.Name(id=self.func_name, ctx=ast.Load()),
                        args=[node], keywords=[])

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            return self.wrap_node(node)
        else:
            return node

    def visit_Num(self, node):
        return self.wrap_node(node)

    def visit_NameConstant(self, node):
        return self.wrap_node(node)

class DictWrapper(ast.NodeTransformer):
    def __init__(self, d):
        self.d = d

    def wrap_node(self, node):
        return ast.Subscript(value=ast.Name(id=self.d, ctx=ast.Load()),
                             slice=ast.Index(value=node, ctx=ast.Load()),
                             ctx=ast.Load())

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            return self.wrap_node(node)
        else:
            return node

    def visit_Num(self, node):
        return self.wrap_node(node)

    def visit_NameConstant(self, node):
        return self.wrap_node(node)

def identity(path, *args, **kwargs):
    source = open(path, 'r').read()
    tree = ast.parse(source, path, 'exec')
    print(ast.dump(tree))
    return compile(tree, path, mode='exec')

def wrap_access(path, func_name):
    source = open(path, 'r').read()
    tree = ast.parse(source, path, 'exec')
    tree = AccessWrapper(func_name).visit(tree)
    ast.fix_missing_locations(tree)
    print(ast.dump(tree))
    return compile(tree, path, mode='exec')

def wrap_dict(path, d):
    source = open(path, 'r').read()
    tree = ast.parse(source, path, 'exec')
    tree = DictWrapper(d).visit(tree)
    ast.fix_missing_locations(tree)
    print(ast.dump(tree))
    return compile(tree, path, mode='exec')

def _wrapper(x):
    return x

class Getter:
    def __getitem__(self, item):
        return item

# namespace = {'_wrapper': _wrapper}
# code_obj = identity('test.py', '_wrapper')
# #code_obj = wrap_access('test.py', '_wrapper')
# start = timer()
# exec(code_obj, namespace)
# print(timer()-start)