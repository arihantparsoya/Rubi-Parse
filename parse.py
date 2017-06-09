import re
from sympy import srepr
from sympy.core.sympify import sympify
from itertools import chain, combinations

full_string = '''
List[RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Times[9, Power[4, -1]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Times[1, Power[4, -1]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], PosQ[Times[b, d, Power[Times[a, c], -1]]]]]], Plus[Times[-4, Power[Times[5, b, Power[Plus[a, Times[b, x]], Times[5, Power[4, -1]]], Power[Plus[c, Times[d, x]], Times[1, Power[4, -1]]]], -1]], Times[-1, d, Power[Times[5, b], -1], Int[Times[1, Power[Times[Power[Plus[a, Times[b, x]], Times[5, Power[4, -1]]], Power[Plus[c, Times[d, x]], Times[5, Power[4, -1]]]], -1]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Times[5, Power[4, -1]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Times[1, Power[4, -1]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], PosQ[Times[b, d, Power[Times[a, c], -1]]]]]], Plus[Times[-2, Power[Times[b, Power[Plus[a, Times[b, x]], Times[1, Power[4, -1]]], Power[Plus[c, Times[d, x]], Times[1, Power[4, -1]]]], -1]], Times[Plus[Times[b, c], Times[-1, a, d]], Power[Times[2, b], -1], Int[Times[1, Power[Times[Power[Plus[a, Times[b, x]], Times[5, Power[4, -1]]], Power[Plus[c, Times[d, x]], Times[5, Power[4, -1]]]], -1]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Times[3, Power[2, -1]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Times[3, Power[2, -1]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]]]]], Times[x, Power[Times[a, c, Sqrt[Plus[a, Times[b, x]]], Sqrt[Plus[c, Times[d, x]]]], -1]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Sqrt[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]]], Sqrt[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]]]]], Times[2, Subst[Int[Times[1, Power[Plus[b, Times[-1, d, Power[x, 2]]], -1]], x], x, Times[Sqrt[Plus[a, Times[b, x]]], Power[Sqrt[Plus[c, Times[d, x]]], -1]]]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Sqrt[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]]], Sqrt[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], PositiveQ[a], ZeroQ[Plus[a, c]]]]], Times[ArcCosh[Times[b, x, Power[a, -1]]], Power[b, -1]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]]]]], Int[Times[1, Power[Plus[Times[a, c], Times[b, d, Power[x, 2]]], -1]], x]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Times[Plus[Optional[Pattern[a, Blank[]]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Plus[Optional[Pattern[c, Blank[]]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]]], -1]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], NonzeroQ[Plus[Times[b, c], Times[-1, a, d]]]]]], Plus[Times[b, Power[Plus[Times[b, c], Times[-1, a, d]], -1], Int[Times[1, Power[Plus[a, Times[b, x]], -1]], x]], Times[-1, d, Power[Plus[Times[b, c], Times[-1, a, d]], -1], Int[Times[1, Power[Plus[c, Times[d, x]], -1]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], -1]], Pattern[x, Blank[Symbol]]], FreeQ[List[a, b], x]]], Times[Log[RemoveContent[Plus[a, Times[b, x]], x]], Power[b, -1]]], RuleDelayed[HoldPattern[Int[Times[1, Power[Pattern[x, Blank[]], -1]], Pattern[x, Blank[Symbol]]]], Log[x]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], PositiveIntegerQ[Plus[m, Times[1, Power[2, -1]]]]]]], Plus[Times[x, Power[Plus[a, Times[b, x]], m], Power[Plus[c, Times[d, x]], m], Power[Plus[Times[2, m], 1], -1]], Times[2, a, c, m, Power[Plus[Times[2, m], 1], -1], Int[Times[Power[Plus[a, Times[b, x]], Plus[m, -1]], Power[Plus[c, Times[d, x]], Plus[m, -1]]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[n, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], IntegerQ[Plus[m, Times[1, Power[2, -1]]]], IntegerQ[Plus[n, Times[1, Power[2, -1]]]], Less[m, n, 0]]]], Plus[Times[-1, Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], Plus[n, 1]], Power[Times[2, a, d, Plus[m, 1]], -1]], Times[Plus[m, n, 2], Power[Times[2, a, Plus[m, 1]], -1], Int[Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], n]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[n, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], IntegerQ[Plus[m, Times[1, Power[2, -1]]]], IntegerQ[Plus[n, Times[1, Power[2, -1]]]], Less[0, m, n]]]], Plus[Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], n], Power[Times[b, Plus[m, n, 1]], -1]], Times[2, c, n, Power[Plus[m, n, 1], -1], Int[Times[Power[Plus[a, Times[b, x]], m], Power[Plus[c, Times[d, x]], Plus[n, -1]]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d, m], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], Not[IntegerQ[Times[2, m]]]]]], Times[Power[Plus[a, Times[b, x]], FracPart[m]], Power[Plus[c, Times[d, x]], FracPart[m]], Power[Power[Plus[Times[a, c], Times[b, d, Power[x, 2]]], FracPart[m]], -1], Int[Power[Plus[Times[a, c], Times[b, d, Power[x, 2]]], m], x]]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], NegativeIntegerQ[Plus[m, Times[3, Power[2, -1]]]]]]], Plus[Times[-1, x, Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], Plus[m, 1]], Power[Times[2, a, c, Plus[m, 1]], -1]], Times[Plus[Times[2, m], 3], Power[Times[2, a, c, Plus[m, 1]], -1], Int[Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], Plus[m, 1]]], x]]]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Optional[Pattern[m, Blank[]]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Optional[Pattern[m, Blank[]]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d, m], x], ZeroQ[Plus[Times[b, c], Times[a, d]]], Or[IntegerQ[m], And[PositiveQ[a], PositiveQ[c]]]]]], Int[Power[Plus[Times[a, c], Times[b, d, Power[x, 2]]], m], x]], RuleDelayed[HoldPattern[Condition[Int[Times[Power[Plus[Optional[Pattern[a, Blank[]]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Optional[Pattern[m, Blank[]]]], Power[Plus[Pattern[c, Blank[]], Times[Optional[Pattern[d, Blank[]]], Pattern[x, Blank[]]]], Pattern[n, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, c, d, m, n], x], NonzeroQ[Plus[Times[b, c], Times[-1, a, d]]], ZeroQ[Plus[m, n, 2]], NonzeroQ[Plus[m, 1]]]]], Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Plus[c, Times[d, x]], Plus[n, 1]], Power[Times[Plus[Times[b, c], Times[-1, a, d]], Plus[m, 1]], -1]]], RuleDelayed[HoldPattern[Condition[Int[Power[Plus[Optional[Pattern[a, Blank[]]], Times[Optional[Pattern[b, Blank[]]], Pattern[u, Blank[]]]], Pattern[m, Blank[]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, m], x], LinearQ[u, x], NonzeroQ[Plus[u, Times[-1, x]]]]]], Times[1, Power[Coefficient[u, x, 1], -1], Subst[Int[Power[Plus[a, Times[b, x]], m], x], x, u]]], RuleDelayed[HoldPattern[Condition[Int[Power[Plus[Optional[Pattern[a, Blank[]]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, m], x], NonzeroQ[Plus[m, 1]]]]], Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Times[b, Plus[m, 1]], -1]]], RuleDelayed[HoldPattern[Condition[Int[Power[Pattern[x, Blank[]], Optional[Pattern[m, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[m, x], NonzeroQ[Plus[m, 1]]]]], Times[Power[x, Plus[m, 1]], Power[Plus[m, 1], -1]]]]
'''


full_string = '''
List[RuleDelayed[HoldPattern[Condition[Int[Times[1, Power[Plus[Pattern[a, Blank[]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], -1]], Pattern[x, Blank[Symbol]]], FreeQ[List[a, b], x]]], Times[Log[RemoveContent[Plus[a, Times[b, x]], x]], Power[b, -1]]], RuleDelayed[HoldPattern[Condition[Int[Power[Plus[Optional[Pattern[a, Blank[]]], Times[Optional[Pattern[b, Blank[]]], Pattern[x, Blank[]]]], Pattern[m, Blank[]]], Pattern[x, Blank[Symbol]]], And[FreeQ[List[a, b, m], x], NonzeroQ[Plus[m, 1]]]]], Times[Power[Plus[a, Times[b, x]], Plus[m, 1]], Power[Times[b, Plus[m, 1]], -1]]], RuleDelayed[HoldPattern[Condition[Int[Power[Pattern[x, Blank[]], Optional[Pattern[m, Blank[]]]], Pattern[x, Blank[Symbol]]], And[FreeQ[m, x], NonzeroQ[Plus[m, 1]]]]], Times[Power[x, Plus[m, 1]], Power[Plus[m, 1], -1]]]]
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
                #default_values[sympify(i[1][1] + '_')] = 1
                default_values[(i[1][1])] = 1

    if parsed[0] == "Plus": # find Default arguments for "Plus"
        for i in parsed[1:]:
            if i[0] == "Optional":
                #default_values[sympify(i[1][1] + '_')] = 0
                default_values[(i[1][1])] = 0

    if parsed[0] == "Power": # find Default arguments for "Power"
        for i in parsed[1:]:
            if i[0] == "Optional":
                #default_values[sympify(i[1][1] + '_')] = 1
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

    if parsed[0] in replacements:
        out += replacements[parsed[0]]
    else:
        out += parsed[0]

    if len(parsed) == 1:
        return out

    out += "("
    out += ", ".join([generate_sympy_from_parsed(i) for i in parsed[1:]])
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

    return string, symbols


def symbols2wilds(string): #Converts `symbols` into `wildcards` in the expression
    expr = sympify(string)
    s = srepr(expr)
    p = r'(Symbol\(\'(\w)\'\))'
    matches = re.findall(p, s)
    for expression, symbol in matches:
        s = s.replace(expression, "(Symbol('" + symbol + "_'" + "))")
    return str(sympy2matchpy(sympify(s), parse_rules=True))


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def srepr2matchpy(string, wildcards=False):
    for i in re.findall(r"(Function\('(\w+)'\))", string):
        string = string.replace(i[0], i[1])

    if wildcards:
        for i in re.findall(r"(Symbol\('(\w+)'\))", string):
            string = string.replace(i[0], i[1] + '_')
    else:
        for i in re.findall(r"(Symbol\('(\w+)'\))", string):
            string = string.replace(i[0], i[1])

    return string


def downvalues_rules(r):
    '''
    Function which generates parsed rules by substituting all possible
    combinations of default values.
    '''
    res = []
    parsed = ""
    index = 0

    for i in r:
        pattern = i[1][1][1]
        d = get_default_values(pattern, {})
        pattern = generate_sympy_from_parsed(pattern.copy())
        pattern, free_symbols = add_wildcards(pattern)
        condition = generate_sympy_from_parsed(i[1][1][2])
        transformed = generate_sympy_from_parsed(i[2])

        for j in powerset(d):
            p = sympify(pattern)
            c = sympify(condition)
            t = sympify(transformed)
            f_symbols = free_symbols.copy()
            for k in j:
                p = p.subs(k + '_', d[k])
                c = c.subs(k, d[k])
                t = t.subs(k, d[k])
                f_symbols.remove(k)

            p = srepr2matchpy(srepr(p))
            c = srepr2matchpy(srepr(c), wildcards=True)
            t = srepr2matchpy(srepr(t))

            index += 1
            parsed = parsed + 'pattern' + str(index) +' = Pattern(' + str(p) + ', cons(' + str(c) + ', '+ str(tuple(f_symbols)).replace("'", "") +'))'
            parsed = parsed + '\n' + 'rule' + str(index) +' = ReplacementRule(' + 'pattern' + str(index) + ', lambda ' + ', '.join(f_symbols) + ' : ' + str(t) + ')\n'
            parsed = parsed + 'rubi.add(rule'+ str(index) +')\n\n'

    return parsed


res = parse_full_form(full_string)
rules = []


for i in res: # seperate all rules
    if i[0] == 'RuleDelayed':
        rules.append(i)


result = downvalues_rules(rules)


print(result)
