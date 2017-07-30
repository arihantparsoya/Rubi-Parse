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
        string = string.replace(i[0], "WC(1, True, '{}', mpyInt({}))".format(i[1], optional[i[1]]))
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
                return 'mpyInt({})'.format(parsed)
        else:
            if symbols==[]:
                try:
                    float(parsed)
                    return 'mpyInt({})'.format(parsed)
                except:
                    return parsed
            elif parsed in symbols:
                return parsed
            else:
                return 'mpyInt({})'.format(parsed)

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

def get_free_symbols(s, symbols, free_symbols=[]):
    if not isinstance(s, list):
        if s in symbols:
            free_symbols.append(s)
        return free_symbols

    if len(s) == 1:
        return free_symbols

    for i in s:
        free_symbols = get_free_symbols(i, symbols)

    return free_symbols

def _divide_constriant(s, symbols):
    # Creates a CustomConstraint of the form `CustomConstraint(lambda a, x: FreeQ(a, x))`
    if s[0] == 'FreeQ':
        return ''
    lambda_symbols = list(set(get_free_symbols(s, symbols, [])))
    return 'CustomConstraint(lambda {}: {})'.format(','.join(lambda_symbols), generate_sympy_from_parsed(s))

def divide_constraint(s, symbols):
    if s[0] == 'And':
        result = [_divide_constriant(i, symbols) for i in s[1:]]
    else:
        result = _divide_constriant(s, symbols)

    r = ['']
    for i in result:
        if i != '':
            r.append(i)

    return ', '.join(r)

def downvalues_rules(r):
    '''
    Function which generates parsed rules by substituting all possible
    combinations of default values.
    '''
    res = []
    parsed = '''
import matchpy
Pattern, ReplacementRule, ManyToOneReplacer = matchpy.Pattern, matchpy.ReplacementRule, matchpy.ManyToOneReplacer

from sympy import Symbol, Pow, Add, Integral, Basic
from matchpy.expressions.functions import register_operation_iterator, register_operation_factory
from matchpy import Operation, CommutativeOperation, AssociativeOperation, OneIdentityOperation, CustomConstraint
from sympy.integrals.rubi.symbol import WC, mpyInt
from sympy.integrals.rubi.constraint import freeQ
from sympy.integrals.rubi.utility_function import FreeQ

Operation.register(Integral)
register_operation_iterator(Integral, lambda a: (a._args[0],) + a._args[1], lambda a: len(a._args))

Operation.register(Pow)
OneIdentityOperation.register(Pow)
register_operation_iterator(Pow, lambda a: a._args, lambda a: len(a._args))

def sympy_op_factory(old_operation, new_operands, variable_name):
     return type(old_operation)(*new_operands)

register_operation_factory(Basic, sympy_op_factory)

A_, B_, C_, a_, b_, c_, d_, e_, f_, g_, h_, i_, j_, k_, l_, m_, n_, p_, q_, r_, s_, w_, x_, z_ = [WC(1, True, i) for i in 'ABCabcdefghijklmnpqrswxz']
mn_ = WC(1, True, 'mn')
non2_ =  WC(1, True, 'non2')

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
            constriant = ''
            transformed = generate_sympy_from_parsed(i[2].copy(), wild=False, symbols=free_symbols)
            FreeQ_vars, FreeQ_x = None, None
        else:
            #constriant = generate_sympy_from_parsed(i[2][2], wild=True, symbols=free_symbols)
            constriant = divide_constraint(i[2][2], free_symbols)
            transformed = generate_sympy_from_parsed(i[2][1].copy(), wild=False, symbols=free_symbols)
            FreeQ_vars, FreeQ_x = seperate_freeq(i[2][2].copy())

        p = pattern
        c = constriant
        t = transformed

        if FreeQ_vars:
            f_c = FreeQ_vars.copy()
        else:
            f_c = []

        f_symbols = free_symbols.copy()
        freeq_c = parse_freeq(f_c, FreeQ_x)

        index += 1
        parsed = parsed + '    pattern' + str(index) +' = Pattern(' + str(p) + '' + freeq_c + '' + str(c) + ')'
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
