import re
from sympy import srepr
from sympy.core.sympify import sympify
from itertools import chain, combinations

with open('downvalues.txt','r') as f_open:
    full_string = f_open.read()

full_string = '''
List[RuleDelayed[HoldPattern[Int[Power[Plus[Pattern[a,Blank[]],Times[Optional[Pattern[b,Blank[]]],Pattern[x,Blank[]]]],-1],Pattern[x,Blank[Symbol]]]],Condition[Times[Log[RemoveContent[Plus[a,Times[b,x]],x]],Power[b,-1]],FreeQ[List[a,b],x]]]]
'''

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

def generate_sympy_from_parsed(parsed):
    out = ""

    if not isinstance(parsed, list):
        return parsed

    if parsed[0] != 'FreeQ':
        if parsed[0] in replacements:
            out += replacements[parsed[0]]
        else:
            out += parsed[0]

        if len(parsed) == 1:
            return out

        result = [generate_sympy_from_parsed(i) for i in parsed[1:]]
        if '' in result:
            result.remove('')

        out += "("
        out += ", ".join(result)
        out += ")"

    return out

def add_wildcards(string):
    symbols = [] # stores symbols present in the expression

    p = r'(Optional\(Pattern\((\w), Blank\)\))'
    matches = re.findall(p, string)
    for i in matches:
        try:
            float(i[1])
            string = string.replace(i[0], i[1])
        except ValueError:
            string = string.replace(i[0], i[1] + '_')
        symbols.append(i[1])

    p = r'(Pattern\((\w), Blank\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], i[1] + '_')
        symbols.append(i[1])

    p = r'(Pattern\((\w), Blank\(Symbol\)\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], i[1] + '_')
        symbols.append(i[1])

    return string, symbols

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def srepr2matchpy(string, wildcards=False):

    for i in re.findall(r"(Function\('(\w+)'\))", string): # replace all ('Function'())
        string = string.replace(i[0], i[1])

    if wildcards: # replace all ('Symbol'())
        for i in re.findall(r"(Symbol\('(\w+)'\))", string):
            string = string.replace(i[0], i[1] + '_')
    else:
        for i in re.findall(r"(Symbol\('(\w+)'\))", string):
            string = string.replace(i[0], i[1])

    for i in re.findall(r"(Rational\(([+-]?(?<!\.)\b[0-9]+\b(?!\.[0-9])), ([+-]?(?<!\.)\b[0-9]+\b(?!\.[0-9]))\))", string): # replace all `Rational(, )` to `Rational(Integer(), Integer())`
        string = string.replace(i[0], 'Integer('+ i[1] + '/' + i[2] +')')

    return string

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

def downvalues_rules(r):
    '''
    Function which generates parsed rules by substituting all possible
    combinations of default values.
    '''
    res = []
    parsed = '''
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
'''
    index = 0

    for i in r:
        if i[1][1][0] == 'Condition':
            pattern = i[1][1][1].copy()
        else:
            pattern = i[1][1].copy()

        d = get_default_values(pattern, {})
        pattern = generate_sympy_from_parsed(pattern.copy())
        pattern, free_symbols = add_wildcards(pattern)
        free_symbols = list(set(free_symbols)) #remove common symbols

        if i[2][0] != 'Condition': # rules without constraints
            condition = 'True'
            transformed = generate_sympy_from_parsed(i[2].copy())
            FreeQ_vars, FreeQ_x = None, None
        else:
            condition = generate_sympy_from_parsed(i[2][2])
            if condition == '':
                condition = 'True'
            transformed = generate_sympy_from_parsed(i[2][1].copy())
            FreeQ_vars, FreeQ_x = seperate_freeq(i[2][2].copy())

        for j in powerset(d):
            p = sympify(pattern)
            c = sympify(condition)
            if FreeQ_vars:
                f_c = FreeQ_vars.copy()
            else:
                f_c = []
            t = sympify(transformed)
            f_symbols = free_symbols.copy()

            for k in j:
                p = p.subs(k + '_', d[k])
                if not isinstance(c, bool):
                    c = c.subs(k, d[k])
                t = t.subs(k, d[k])
                f_symbols.remove(k)
                if k in f_c:
                    f_c.remove(k)

            p = srepr2matchpy(srepr(p))
            c = srepr2matchpy(srepr(c), wildcards=True)
            t = srepr2matchpy(srepr(t))
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
