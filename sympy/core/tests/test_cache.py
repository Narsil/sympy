from sympy.core.cache import cacheit
from sympy.core.symbol import Symbol, symbols

def test_cacheit_doc():
    @cacheit
    def testfn():
        "test docstring"
        pass

    assert testfn.__doc__ == "test docstring"
    assert testfn.__name__ == "testfn"

def test_symbol():
    x = Symbol('x')
    y = Symbol('x')
    assert x == y

    x, y = symbols('x,x')
    assert x == y
