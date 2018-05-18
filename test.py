import ast
import sys
import inspect
import unittest

from parse import to_source, compare_ast, max_depth

def src_to_tree(*src, mode='exec'):
    return [ast.parse(s, mode=mode) for s in src]

def src_to_src(*src, mode='exec'):
    return [to_source(ast.parse(s, mode=mode)) for s in src]

def src_to_src_to_tree(*src, mode='exec'):
    return [ast.parse(to_source(ast.parse(s, mode=mode)), mode=mode) for s in src]

def compare_trees(trees1, trees2):
    return all(compare_ast(t1, t2) for t1, t2 in zip(trees1, trees2))


# Test compare_ast
class TestASTComparison(unittest.TestCase):
    def test_identity(self):
        src = inspect.getsource(inspect.getmodule(self.__class__))
        tree = ast.parse(src)
        self.assertTrue(compare_ast(tree, tree))


class TestAtoms(unittest.TestCase):
    # Test various numbers
    def test_Num(self):
        src = ['1', '1+1j', '0xff']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test various strings
    def test_Str(self):
        src = ["'a'", "'a %s'%b", "'\\n'"]
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test byte strings
    def test_Bytes(self):
        src = ["b'a'", "b'\\x00 \\n'"]
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test the True, False, None, and Ellipsis constants
    def test_NamedConstant(self):
        src = ['True', 'False', 'None', '...']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test Name access, and Starred access
    def test_Var(self):
        src = ['a', '*a']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test lists, tuples, sets, and dictionaries
    def test_Iterable(self):
        src = ['[a, [b, c]]', '(a, (b, c))', '{a, {b, c}}', '{a: b, **c}']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))


# Test various miscellaneous expressions, like that produced by mode=eval(), and if expressions
class TestExpressions(unittest.TestCase):
    # Test container expressions, which contain operators
    def test_Expr(self):
        tree = ast.Expr(value=ast.Name(id='a', ctx=ast.Load()))
        src = to_source(tree)
        self.assertEqual(src, 'a')

    # Test the type of node returned by mode=eval
    def test_Expression(self):
        tree = ast.Expression(body=ast.Name(id='a', ctx=ast.Load()))
        src = to_source(tree)
        self.assertEqual(src, 'a')

    # Test if expressions
    def test_IfExp(self):
        src = 'a if b else c'
        tree = src_to_tree(src)
        rtt = src_to_src_to_tree(src)
        self.assertTrue(compare_ast(tree, rtt))


# Test proper parsing of unary operations
class TestUnaryOps(unittest.TestCase):
    # Test that unary operations are round-tripped correctly when left of power operations
    def test_priority(self):
        src = ['-1**2', '(-1)**2']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))

    # Test that a unary operator on the right of a power operator binds more tightly
    def test_binding(self):
        src1, expected = '2**(-1)', '2**-1'
        result = src_to_src(src1)[0]
        self.assertEqual(expected, result)


# Test binary arithmetic operators
class TestBinaryOps(unittest.TestCase):
    # Test that priority is preserved through round-tripping
    def test_priority(self):
        src = ['a*(b+c)', 'a*b+c', '(b+c//d)/e', 'b-c/d', '(a+b)%c', 'a+b%c',
               '((((((a|b)^c)&d)<<e>>f)+g-h)*i@j/k//l%m)**n', 'a|b^c&d<<e>>f+g-h*i@j/k//l%m**n']
        result = src_to_src(*src)
        self.assertEqual(src, result)

    # Test to ensure left-associative operations like division and modulo behave properly
    def test_special_ops(self):
        src = ['a-(b-c)', 'a-b-c', 'a//(b/c)', 'a//b/c', 'a/(b%c)', 'a/b%c', 'a%(b/c)', 's%b/c']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))


# Test boolean operators
class TestBooleanOps(unittest.TestCase):
    # Test priority with other operators
    def test_priority(self):
        src = ['not a and b', 'not (a and b)+c', '(not (a and b))+c',
               'a and b or c', 'a and (b or c)']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))


# Test comparison expressions
class TestComparison(unittest.TestCase):
    # Test the priority relative to other operators, as well as other comparisons
    def test_priority(self):
        src = ['a>b+c', '(a>b)+c', 'a>b>c', '(a>b)>c', '(a is  b) > c']
        trees = src_to_tree(*src)
        rtt = src_to_src_to_tree(*src)
        self.assertTrue(compare_trees(trees, rtt))


# Test various forms of subscription, such as attribute access and slicing
class TestSubscripting(unittest.TestCase):
    # Test attribute access
    def test_attribute(self):
        src = 'a.b'
        result = src_to_src(src)[0]
        self.assertEqual(src, result)

    # Test indexing & slicing
    def test_slicing(self):
        src = ['a[b]', 'a[b:]', 'a[:b]', 'a[::b]', 'a[b::c]', 'a[b:c]', 'a[:b:c]', 'a[b:c:d]']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)

    # Test extended slicing
    def test_extended_slicing(self):
        src = ['a[b:, c]', 'a[:b, c]', 'a[::b, c]', 'a[b::c, d]', 'a[b:c, d]', 'a[:b:c, d]', 'a[b:c:d, c]']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)


# Test list, dictionary, generator & list comprehensions
class TestComprehensions(unittest.TestCase):
    def test_ListComp(self):
        src = ['[a for a in b]', '[c for a in b for c in a]', '[d**f for a in b if a>c for d in a if d<e]']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)

    def test_SetComp(self):
        src = ['{a for a in b}', '{c for a in b for c in a}', '{d**f for a in b if a>c for d in a if d<e}']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)

    def test_GeneratorComp(self):
        src = ['(a for a in b)', '(c for a in b for c in a)', '(d**f for a in b if a>c for d in a if d<e)']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)

    def test_DictComp(self):
        src = ['{a:a**2 for a in b}', '{c:c**2 for a in b for c in a}', '{d:d**2 for a in b if a>c for d in a if d<e}']
        for s in src:
            result = src_to_src(s)[0]
            self.assertEqual(s, result)

    def test_async_comprehension(self):
        tree = ast.comprehension(target=ast.Name(id='a', ctx=ast.Store()), iter=ast.Name(id='b', ctx=ast.Load()),
                                 ifs=[], is_async=True)
        expected = 'async for a in b'
        result = to_source(tree)
        self.assertEqual(expected, result)


class TestFunctions(unittest.TestCase):
    def test_keyword(self):
        tree = ast.keyword(arg='abc', value=ast.Name(id='def', ctx=ast.Load()))
        src = to_source(tree)
        self.assertEqual(src, 'abc=def')

    def test_call(self):
        src = ['f()', 'f(a, b)', 'f(a, *b)', 'f(a, b=c)', 'f(a, b=c, *d, **e)']
        for s in src:
            tree = src_to_tree(s)
            rtt = src_to_src_to_tree(s)
            self.assertTrue(compare_ast(tree, rtt))


if __name__ == '__main__':
    unittest.main()
