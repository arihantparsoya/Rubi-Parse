
from matchpy import Wildcard, Pattern, ReplacementRule, ManyToOneReplacer
from .operation import *
from .symbol import VariableSymbol, Integer
from .constraint import cons

a, b, c, d, e, f, g, h, x, u = map(VariableSymbol, 'abcdefghxu')
n, m = map(VariableSymbol, 'nm')
zoo = VariableSymbol('zoo')

a_, b_, c_, d_, e_, f_, g_, h_ = map(Wildcard.dot, 'abcdefgh')
n_, m_ = map(Wildcard.dot, 'nm')
x_, u_ = map(Wildcard.symbol, 'xu')


def rubi_object():
    rubi = ManyToOneReplacer()
    pattern1 = Pattern(Int(Pow(x_, Integer(-1)), x_), cons(True, (x,)))
    rule1 = ReplacementRule(pattern1, lambda x : Log(x))
    rubi.add(rule1)

    return rubi
