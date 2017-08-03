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
        string = string.replace(i[0], "WC(1, True, '{}', S('{}'))".format(i[1], optional[i[1]]))
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
        res.append(('CustomConstraint(lambda {}, {}: FreeQ({}, {}))').format(i, x, i, x))
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
                return "S('{}')".format(parsed)
        else:
            if symbols==[]:
                try:
                    float(parsed)
                    return "S('{}')".format(parsed)
                except:
                    return parsed
            elif parsed in symbols:
                return parsed
            else:
                return "S('{}')".format(parsed)

    if parsed[0] == 'Rational':
        return 'S({})/S({})'.format(generate_sympy_from_parsed(parsed[1]), generate_sympy_from_parsed(parsed[2]))
    elif parsed[0] != 'FreeQ':
        if parsed[0] in replacements:
            out += replacements[parsed[0]]
        else:
            if parsed[0] == 'Int':
                out += 'Integral'
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

    for i in s:
        free_symbols = get_free_symbols(i, symbols, free_symbols)

    return free_symbols

def _divide_constriant(s, symbols):
    # Creates a CustomConstraint of the form `CustomConstraint(lambda a, x: FreeQ(a, x))`
    if s[0] == 'FreeQ':
        return ''
    lambda_symbols = list(set(get_free_symbols(s, symbols, [])))
    return 'CustomConstraint(lambda {}: {})'.format(', '.join(lambda_symbols), generate_sympy_from_parsed(s))

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

from sympy import Symbol, Pow, Add, Integral, Basic, Mul, S, Or, And
from matchpy.expressions.functions import register_operation_iterator, register_operation_factory
from matchpy import Operation, CommutativeOperation, AssociativeOperation, OneIdentityOperation, CustomConstraint
from sympy.integrals.rubi.symbol import WC
from sympy.integrals.rubi.utility_function import (Int, Set, With, Scan, MapAnd, FalseQ, ZeroQ, NegativeQ, NonzeroQ, FreeQ, List, Log, PositiveQ, PositiveIntegerQ, NegativeIntegerQ, IntegerQ, IntegersQ, ComplexNumberQ, RealNumericQ, PositiveOrZeroQ, NegativeOrZeroQ, FractionOrNegativeQ, NegQ, Equal, Unequal, IntPart, FracPart, RationalQ, ProductQ, SumQ, NonsumQ, Subst, First, Rest, SqrtNumberQ, SqrtNumberSumQ, LinearQ, Sqrt, ArcCosh, Coefficient, Denominator, Hypergeometric2F1, ArcTan, Not, Simplify, FractionalPart, IntegerPart, AppellF1, EllipticPi, EllipticE, EllipticF, ArcTan, ArcTanh, ArcSin, ArcSinh, ArcCos, ArcCsc, ArcCsch, Sinh, Tanh, Cosh, Sech, Csch, Coth, LessEqual, Less, Greater, GreaterEqual, FractionQ, IntLinearcQ, Expand, IndependentQ, PowerQ, IntegerPowerQ, PositiveIntegerPowerQ, FractionalPowerQ, AtomQ, ExpQ, LogQ, Head, MemberQ, TrigQ, SinQ, CosQ, TanQ, CotQ, SecQ, CscQ, HyperbolicQ, SinhQ, CoshQ, TanhQ, CothQ, SechQ, CschQ, InverseTrigQ, SinCosQ, SinhCoshQ, Rt, LeafCount, Numerator, NumberQ, NumericQ, Length, ListQ, Im, Re, InverseHyperbolicQ, InverseFunctionQ, TrigHyperbolicFreeQ, InverseFunctionFreeQ, RealQ, EqQ, FractionalPowerFreeQ, ComplexFreeQ, PolynomialQ, FactorSquareFree, PowerOfLinearQ, Exponent, QuadraticQ, LinearPairQ, BinomialParts, TrinomialParts, PolyQ, EvenQ, OddQ, PerfectSquareQ, NiceSqrtAuxQ, NiceSqrtQ, Together, FixSimplify, TogetherSimplify, PosAux, PosQ, CoefficientList, ReplaceAll, ExpandLinearProduct, GCD, ContentFactor, NumericFactor, NonnumericFactors, MakeAssocList, GensymSubst, KernelSubst, ExpandExpression, Apart, SmartApart, MatchQ, PolynomialQuotientRemainder, FreeFactors, NonfreeFactors, RemoveContentAux, RemoveContent, FreeTerms, NonfreeTerms, ExpandAlgebraicFunction, CollectReciprocals, ExpandCleanup, AlgebraicFunctionQ, Coeff, LeadTerm, RemainingTerms, LeadFactor, RemainingFactors, LeadBase, LeadDegree, Numer, Denom, hypergeom, Expon, MergeMonomials, PolynomialDivide, BinomialQ, TrinomialQ, GeneralizedBinomialQ, GeneralizedTrinomialQ, FactorSquareFreeList, PerfectPowerTest, SquareFreeFactorTest, RationalFunctionQ, RationalFunctionFactors, NonrationalFunctionFactors, Reverse, RationalFunctionExponents, RationalFunctionExpand, ExpandIntegrand, SimplerQ, SimplerSqrtQ, SumSimplerQ, SumSimplerAuxQ, BinomialDegree, TrinomialDegree, CancelCommonFactors, SimplerIntegrandQ, GeneralizedBinomialDegree, GeneralizedBinomialParts, GeneralizedTrinomialDegree, GeneralizedTrinomialParts, MonomialQ, MonomialSumQ, MinimumMonomialExponent, MonomialExponent, LinearMatchQ, PowerOfLinearMatchQ, QuadraticMatchQ, CubicMatchQ, BinomialMatchQ, TrinomialMatchQ, GeneralizedBinomialMatchQ, GeneralizedTrinomialMatchQ, QuotientOfLinearsMatchQ, PolynomialTermQ, PolynomialTerms, NonpolynomialTerms, PseudoBinomialParts, NormalizePseudoBinomial, PseudoBinomialPairQ, PseudoBinomialQ, PolynomialGCD, PolyGCD, AlgebraicFunctionFactors, NonalgebraicFunctionFactors, QuotientOfLinearsP, QuotientOfLinearsParts, QuotientOfLinearsQ, Flatten, Sort, AbsurdNumberQ, AbsurdNumberFactors, NonabsurdNumberFactors, SumSimplerAuxQ, SumSimplerQ, Prepend, Drop, CombineExponents, FactorInteger, FactorAbsurdNumber, SubstForInverseFunction, SubstForFractionalPower, SubstForFractionalPowerOfQuotientOfLinears, FractionalPowerOfQuotientOfLinears, SubstForFractionalPowerQ, SubstForFractionalPowerAuxQ, FractionalPowerOfSquareQ, FractionalPowerSubexpressionQ, Apply, FactorNumericGcd, MergeableFactorQ, MergeFactor, MergeFactors, TrigSimplifyQ, TrigSimplify, Order, FactorOrder, Smallest, OrderedQ, MinimumDegree, PositiveFactors, Sign, NonpositiveFactors, PolynomialInAuxQ, PolynomialInQ, ExponentInAux, ExponentIn, PolynomialInSubstAux, PolynomialInSubst, Distrib, DistributeDegree, FunctionOfPower, DivideDegreesOfFactors, MonomialFactor, FullSimplify, FunctionOfLinearSubst, FunctionOfLinear, NormalizeIntegrand, NormalizeIntegrandAux, NormalizeIntegrandFactor, NormalizeIntegrandFactorBase, NormalizeTogether, NormalizeLeadTermSigns, AbsorbMinusSign, NormalizeSumFactors, SignOfFactor, NormalizePowerOfLinear, SimplifyIntegrand, SimplifyTerm, TogetherSimplify, SmartSimplify, SubstForExpn, ExpandToSum, UnifySum, UnifyTerms, UnifyTerm, CalculusQ, FunctionOfInverseLinear, PureFunctionOfSinhQ, PureFunctionOfTanhQ, PureFunctionOfCoshQ, IntegerQuotientQ, OddQuotientQ, EvenQuotientQ, FindTrigFactor, FunctionOfSinhQ, FunctionOfCoshQ, OddHyperbolicPowerQ, FunctionOfTanhQ, FunctionOfTanhWeight, FunctionOfHyperbolicQ, SmartNumerator, SmartDenominator, SubstForAux, ActivateTrig, ExpandTrig, TrigExpand, SubstForTrig, SubstForHyperbolic, InertTrigFreeQ, LCM, SubstForFractionalPowerOfLinear, FractionalPowerOfLinear, InverseFunctionOfLinear, InertTrigQ, InertReciprocalQ, ActivateTrig, DeactivateTrig, FixInertTrigFunction, DeactivateTrigAux, DeactivateTrigAux, PowerOfInertTrigSumQ, PiecewiseLinearQ, KnownTrigIntegrandQ, KnownSineIntegrandQ, KnownTangentIntegrandQ, KnownCotangentIntegrandQ, KnownSecantIntegrandQ, ExpandTrigExpand, ExpandTrigReduce, TryPureTanSubst, TryTanhSubst, TryPureTanhSubst, AbsurdNumberGCD, AbsurdNumberGCDList, Map2, ConstantFactor, SameQ, ReplacePart, CommonFactors, MostMainFactorPosition, FunctionOfExponentialQ, FunctionOfExponential, FunctionOfExponentialFunction, FunctionOfExponentialFunctionAux, FunctionOfExponentialTest, FunctionOfExponentialTestAux)

Operation.register(Integral)
register_operation_iterator(Integral, lambda a: (a._args[0],) + a._args[1], lambda a: len((a._args[0],) + a._args[1]))

Operation.register(Pow)
OneIdentityOperation.register(Pow)
register_operation_iterator(Pow, lambda a: a._args, lambda a: len(a._args))

Operation.register(Add)
OneIdentityOperation.register(Add)
CommutativeOperation.register(Add)
AssociativeOperation.register(Add)
register_operation_iterator(Add, lambda a: a._args, lambda a: len(a._args))

Operation.register(Mul)
OneIdentityOperation.register(Mul)
CommutativeOperation.register(Mul)
AssociativeOperation.register(Mul)
register_operation_iterator(Mul, lambda a: a._args, lambda a: len(a._args))

def sympy_op_factory(old_operation, new_operands, variable_name):
     return type(old_operation)(*new_operands)

register_operation_factory(Basic, sympy_op_factory)

a = Symbol('a')
x = Symbol('x')

A_, B_, C_, a_, b_, c_, d_, e_, f_, g_, h_, i_, j_, k_, l_, m_, n_, p_, q_, r_, t_, u_, s_, w_, x_, z_ = [WC(1, True, i) for i in 'ABCabcdefghijklmnpqrtuswxz']
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
#result = result.replace('Int(',  'Integral(')

f = open("patterns.py","w")
f.write(result)
f.close()
