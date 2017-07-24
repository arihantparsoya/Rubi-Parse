import re

with open('downvalues.txt','r') as f_open:
    full_string = f_open.read()

replacements = dict(
        Times="Mul",
        Plus="Add",
        Power="Pow",
)

def parse_full_form(wmexpr):
    out = []
    stack = [out]
    generator = re.finditer(r'[\[\],]', wmexpr)
    last_pos = 0
    for match in generator:
        if match is None:
            break
        position = match.start()
        last_expr = wmexpr[last_pos:position].replace(',', '').replace(']', '').replace('[', '').strip()

        if match.group() == ',':
            if last_expr != '':
                stack[-1].append(last_expr)
        elif match.group() == ']':
            if last_expr != '':
                stack[-1].append(last_expr)
            stack.pop()
            current_pos = stack[-1]
        elif match.group() == '[':
            stack[-1].append([last_expr])
            stack.append(stack[-1][-1])
        last_pos = match.end()
    return out[0]

def get_default_values(parsed, default_values={}):
    '''
    Returns default values which exist in the pattern
    '''

    if not isinstance(parsed, list):
        return default_values

    if parsed[0] == "Times": # find Default arguments for "Times"
        for i in parsed[1:]:
            if i[0] == "Optional":
                default_values[(i[1][1])] = 1

    if parsed[0] == "Plus": # find Default arguments for "Plus"
        for i in parsed[1:]:
            if i[0] == "Optional":
                default_values[(i[1][1])] = 0

    if parsed[0] == "Power": # find Default arguments for "Power"
        for i in parsed[1:]:
            if i[0] == "Optional":
                default_values[(i[1][1])] = 1

    if len(parsed) == 1:
        return default_values

    for i in parsed:
        default_values = get_default_values(i, default_values)

    return default_values


def add_wildcards(string, optional={}):
    symbols = [] # stores symbols present in the expression

    p = r'(Optional\(Pattern\((\w+), Blank\)\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], "Wildcard.optional('{}', matchpyInteger({}))".format(i[1], optional[i[1]]))
        symbols.append(i[1])

    p = r'(Pattern\((\w+), Blank\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], i[1] + '_')
        symbols.append(i[1])

    p = r'(Pattern\((\w+), Blank\(Symbol\)\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], i[1] + '_')
        symbols.append(i[1])

    return string, symbols

def seperate_freeq(s, variables=[], x=None):
    if s[0] == 'FreeQ':
        if len(s[1]) == 1:
            variables = [s[1]]
        else:
            variables = s[1][1:]
        x = s[2]
    else:
        for i in s[1:]:
            variables, x = seperate_freeq(i, variables, x)
    return variables, x

def parse_freeq(l, x):
    res = []
    for i in l:
        res.append(('FreeQ({}, {})').format(i, x))
    if res != []:
        return ', ' + ', '.join(res)
    return ''

def generate_sympy_from_parsed(parsed, wild=False, symbols=[]):
    out = ""

    if not isinstance(parsed, list):
        if wild:
            if (parsed in symbols):
                return parsed + '_'
            else:
                return 'matchpyInteger({})'.format(parsed)
        else:
            if symbols==[]:
                try:
                    float(parsed)
                    return 'matchpyInteger({})'.format(parsed)
                except:
                    return parsed
            elif parsed in symbols:
                return parsed
            else:
                return 'matchpyInteger({})'.format(parsed)

    if parsed[0] != 'FreeQ':
        if parsed[0] in replacements:
            out += replacements[parsed[0]]
        else:
            out += parsed[0]

        if len(parsed) == 1:
            return out

        result = [generate_sympy_from_parsed(i, wild=wild, symbols=symbols) for i in parsed[1:]]
        if '' in result:
            result.remove('')

        out += "("
        out += ", ".join(result)
        out += ")"

    return out

def downvalues_rules(r):
    '''
    Function which generates parsed rules by substituting all possible
    combinations of default values.
    '''
    res = []
    parsed = '''
from sympy.external import import_module
matchpy = import_module("matchpy")

if matchpy:
    Wildcard, Pattern, ReplacementRule, ManyToOneReplacer = matchpy.Wildcard, matchpy.Pattern, matchpy.ReplacementRule, matchpy.ManyToOneReplacer
else:
    Wildcard, Pattern, ReplacementRule, ManyToOneReplacer = object, object, object, object
    class Wildcard(object):
        def __init__(self):
            pass
        @staticmethod
        def dot(x):
            pass
        @staticmethod
        def symbol(x):
            pass
    class Pattern(object):
        def __init__(self, a, b):
            pass

from sympy.integrals.rubi.operation import (Int, Mul, Add, Pow, And, Or, ZeroQ, NonzeroQ, List, Log, RemoveContent, PositiveIntegerQ, NegativeIntegerQ, PositiveQ, IntegerQ, IntegersQ, PosQ, NegQ, FracPart, IntPart, RationalQ, Subst, LinearQ, Sqrt, NegativeQ, ArcCosh, Rational, Less, Not, Simplify, Denominator, Coefficient, SumSimplerQ, Equal, Unequal, SimplerQ, LessEqual, IntLinearcQ, Greater, GreaterEqual, FractionQ, ExpandIntegrand, With, Set, Hypergeometric2F1, TogetherSimplify, Inequality, PerfectSquareQ, EvenQ, OddQ, EqQ, NiceSqrtQ, IntQuadraticQ, If, LeafCount, QuadraticQ, LinearMatchQ, QuadraticMatchQ, AtomQ, SplitProduct, SumBaseQ, NegSumBaseQ, IntBinomialQ, LinearPairQ, SimplerSqrtQ, PseudoBinomialPairQ, Rt, PolynomialQ, BinomialQ, BinomialMatchQ, BinomialDegree, GeneralizedBinomialQ, GeneralizedBinomialMatchQ, TrinomialQ, TrinomialMatchQ, GeneralizedTrinomialQ, GeneralizedTrinomialMatchQ, GeneralizedTrinomialDegree, PolyQ, Coeff, SumQ, Expon)
from sympy.integrals.rubi.symbol import VariableSymbol, matchpyInteger
from sympy.integrals.rubi.constraint import cons, FreeQ
from sympy.utilities.decorator import doctest_depends_on

A, B, C, a, b, c, d, e, f, g, h, i, j, k, x, u, v, w, p, q, r, s, z = map(VariableSymbol, 'ABCabcdefghijkxuvwpqrsz')
n, m = map(VariableSymbol, 'nm')
zoo = VariableSymbol('zoo')
mn = VariableSymbol('mn')
non2 = VariableSymbol('non2')
a1 = VariableSymbol('a1')
a2 = VariableSymbol('a2')
b1 = VariableSymbol('b1')
b2 = VariableSymbol('b2')
c1 = VariableSymbol('c1')
c2 = VariableSymbol('c2')
d1 = VariableSymbol('d1')
d2 = VariableSymbol('d2')
e1 = VariableSymbol('e1')
e2 = VariableSymbol('e2')
f1 = VariableSymbol('f1')
f2 = VariableSymbol('f2')
n2 = VariableSymbol('n2')
n3 = VariableSymbol('n3')
Pq = VariableSymbol('Pq')
Px = VariableSymbol('Px')
jn = VariableSymbol('jn')

A_, B_, C_, a_, b_, c_, d_, e_, f_, g_, h_, i_, j_, k_, p_, q_, r_, s_, w_, z_ = map(Wildcard.dot, 'ABCabcdefghijkpqrswz')
n_, m_ = map(Wildcard.dot, 'nm')
mn_ = Wildcard.dot('mn')
non2_ = Wildcard.dot('non2')
a1_ = Wildcard.dot('a1')
a2_ = Wildcard.dot('a2')
b1_ = Wildcard.dot('b1')
b2_ = Wildcard.dot('b2')
c1_ = Wildcard.dot('c1')
c2_ = Wildcard.dot('c2')
d1_ = Wildcard.dot('d1')
d2_ = Wildcard.dot('d2')
n2_ = Wildcard.dot('n2')
e1_ = Wildcard.dot('e1')
e2_ = Wildcard.dot('e2')
f1_ = Wildcard.dot('f1')
f2_ = Wildcard.dot('f2')
n1_ = Wildcard.dot('n1')
n2_ = Wildcard.dot('n2')
n3_ = Wildcard.dot('n3')
Pq_ = Wildcard.dot('Pq')
Px_ = Wildcard.dot('Px')
jn_ = Wildcard.dot('jn')
x_, u_, v_ = map(Wildcard.symbol, 'xuv')

def rubi_object():
    rubi = ManyToOneReplacer()

'''
    index = 0
    for i in r:
        print('parsing rule {}'.format(r.index(i) + 1))

        if i[1][1][0] == 'Condition':
            p = i[1][1][1].copy()
        else:
            p = i[1][1].copy()

        optional = get_default_values(p, {})
        pattern = generate_sympy_from_parsed(p.copy())
        pattern, free_symbols = add_wildcards(pattern, optional=optional)
        free_symbols = list(set(free_symbols)) #remove common symbols
        if i[2][0] != 'Condition': # rules without constraints
            condition = 'True'
            transformed = generate_sympy_from_parsed(i[2].copy(), wild=False, symbols=free_symbols)
            FreeQ_vars, FreeQ_x = None, None
        else:
            condition = generate_sympy_from_parsed(i[2][2], wild=True, symbols=free_symbols)
            if condition == '':
                condition = 'True'
            transformed = generate_sympy_from_parsed(i[2][1].copy(), wild=False, symbols=free_symbols)
            FreeQ_vars, FreeQ_x = seperate_freeq(i[2][2].copy())

        p = pattern
        c = condition
        t = transformed

        if FreeQ_vars:
            f_c = FreeQ_vars.copy()
        else:
            f_c = []

        f_symbols = free_symbols.copy()
        freeq_c = parse_freeq(f_c, FreeQ_x)

        index += 1
        parsed = parsed + '    pattern' + str(index) +' = Pattern(' + str(p) + '' + freeq_c + ', cons(' + str(c) + ', '+ str(tuple(f_symbols)).replace("'", "") +'))'
        parsed = parsed + '\n    ' + 'rule' + str(index) +' = ReplacementRule(' + 'pattern' + str(index) + ', lambda ' + ', '.join(f_symbols) + ' : ' + str(t) + ')\n    '
        parsed = parsed + 'rubi.add(rule'+ str(index) +')\n\n'

    parsed = parsed + '    return rubi\n'
    return parsed

res = parse_full_form(full_string)
rules = []

for i in res: # separate all rules
    if i[0] == 'RuleDelayed':
        rules.append(i)

result = downvalues_rules(rules)

f = open("patterns.py","w")
f.write(result)
f.close()
