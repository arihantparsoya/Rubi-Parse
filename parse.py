import re
from sympy import sympify, Function, Set, Symbol
from sympy.printing import sstr, StrPrinter

StrPrinter._print_Not = lambda self, expr: "Not(%s)" % self._print(expr.args[0])

replacements = dict(
        Times="Mul",
        Plus="Add",
        Power="Pow",
        Log='log',
        Sqrt='sqrt',
        Cos='cos',
        Sin='sin',
        Tan='tan',
        Cot='cot',
        Sec='sec',
        Csc='csc',
        ArcSin='asin',
        ArcCos='acos',
        #ArcTan='atan',
        ArcCot='acot',
        ArcSec='asec',
        ArcCsc='acsc',
        Sinh='sinh',
        Tanh='tanh',
        Coth='coth',
        Sech='sech',
        Csch='csch',
        ArcSinh='asinh',
        ArcCosh='acosh',
        ArcTanh='atanh',
        ArcCoth='acoth',
        ArcSech='asech',
        ArcCsch='acsch',
        Expand='expand',
        Im='im',
        Re='re',
        Together='together',
        Flatten='flatten',
        Polylog='polylog',
        Cancel='cancel',
        #Gamma='gamma',
        TrigExpand='expand_trig',
        Sign='sign',
        Simplify='simplify',
        Defer='UnevaluatedExpr',
)

temporary_variable_replacement = { # Temporarily rename because it can raise errors while sympifying
        'Sum' : "_Sum",
        'gcd' : "_gcd",
        'jn' : "_jn",
}

permanent_variable_replacement = { # Permamenely rename these variables
    "\[ImaginaryI]" : 'ImaginaryI',
    "$UseGamma": '_UseGamma',
}

def parse_full_form(wmexpr):
    '''
    Parses FullForm[Downvalues[]] generated by Mathematica
    '''
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
    Returns Optional variables and their values in the pattern
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
    '''
    replaces `Pattern(variable)` by `variable` in string
    returns the free symbols present in the string
    '''

    symbols = [] # stores symbols present in the expression

    p = r'(Optional\(Pattern\((\w+), Blank\)\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], "WC('{}', S({}))".format(i[1], optional[i[1]]))
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
    '''
    Helper function for parse_freeq()
    '''
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

def parse_freeq(l, x, symbols=None):
    '''
    Divies FreeQ() constraint into smaller constraints.
    '''
    res = []
    for i in l:
        if isinstance(i, str):
            res.append(('CustomConstraint(lambda {}, {}: FreeQ({}, {}))').format(i, x, i, x))
        elif isinstance(i, list):
            s = list(set(get_free_symbols(i, symbols)))
            s = ', '.join(s)
            res.append(('CustomConstraint(lambda {}: FreeQ({}, {}))').format(s, generate_sympy_from_parsed(i), x))
    if res != []:
        return ', ' + ', '.join(res)
    return ''

def generate_sympy_from_parsed(parsed, wild=False, symbols=[], replace_Int=False, parse_FreeQ=True):
    '''
    Parses list into Python syntax

    wild: when set to True, the symbols are replaced as wild symbols
    symbols: Symbols already present in the pattern.
    replace_Int: when set to True, `Int` is replaced by `Integral`(used to parse pattern).
    '''
    out = ""

    if not isinstance(parsed, list):
        try: #return S(number) if parsed is Number
            float(parsed)
            return "S({})".format(parsed)
        except:
            pass
        if parsed in symbols:
            if wild:
                return parsed + '_'
        return parsed

    if parsed[0] == 'Rational':
        return 'S({})/S({})'.format(generate_sympy_from_parsed(parsed[1], wild=wild, symbols=symbols, replace_Int=replace_Int), generate_sympy_from_parsed(parsed[2], wild=wild, symbols=symbols, replace_Int=replace_Int))
    elif parsed[0] != 'FreeQ': # FreeQ is parsed seperately
        if parsed[0] in replacements:
            out += replacements[parsed[0]]
        else:
            if parsed[0] == 'Int' and replace_Int:
                out += 'Integral'
            else:
                out += parsed[0]

        if len(parsed) == 1:
            return out

        result = [generate_sympy_from_parsed(i, wild=wild, symbols=symbols, replace_Int=replace_Int) for i in parsed[1:]]
        if '' in result:
            result.remove('')

        out += "("
        out += ", ".join(result)
        out += ")"

    return out

def get_free_symbols(s, symbols, free_symbols=[]):
    '''
    Returns free symbols present in `s`.
    '''
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
    return 'CustomConstraint(lambda {}: {})'.format(', '.join(lambda_symbols), sstr(sympify(generate_sympy_from_parsed(s)), sympy_integers=True))

def divide_constraint(s, symbols):
    '''
    Divides multiple constraints into smaller constraints.
    '''
    if s[0] == 'And':
        result = [_divide_constriant(i, symbols) for i in s[1:]]
    else:
        result = [_divide_constriant(s, symbols)]

    r = ['']
    for i in result:
        if i != '':
            r.append(i)

    return ', '.join(r)

def setWC(string):
    '''
    Replaces `WC(a, b)` by `WC('a', S(b))`
    '''
    p = r'(WC\((\w+), S\(([-+]?\d)\)\))'
    matches = re.findall(p, string)
    for i in matches:
        string = string.replace(i[0], "WC('{}', S({}))".format(i[1], i[2]))

    return string

def setWith(s, symbols, i):
    if type(s) == Function('With') or type(s) == Function('Module'):
        constraints = ', '
        result = '    def With{}({}):'.format(i, ', '.join(symbols))
        if type(s.args[0]) == Function('List'): # get all local varibles of With and Module
            L = list(s.args[0].args)
        else:
            L = [s.args[0]]

        for i in L: # define local variables
            if isinstance(i, Set):
                result += '\n        {} = {}'.format(i.args[0], sstr(i.args[1], sympy_integers=True))
            elif isinstance(i, Symbol):
                result += "\n        {} = Symbol('{}')".format(i, i)

        if type(s.args[1]) == Function('CompoundExpression'): # Expand CompoundExpression
            C = s.args[1]
            if isinstance(C.args[0], Set):
                result += '\n        {} = {}'.format(C.args[0].args[0], C.args[0].args[1])
            result += '\n        return {}'.format(sstr(C.args[1], sympy_integers=True))
            return result, constraints
        elif type(s.args[1]) == Function('Condition'):
            C = s.args[1]
            if len(C.args) == 2:
                constraints += 'CustomConstraint(lambda {}: {})'.format(', '.join([str(i) for i in C.free_symbols]), sstr(C.args[1], sympy_integers=True))
            result += '\n        return {}'.format(sstr(C.args[0], sympy_integers=True))
            return result, constraints

        result += '\n        return {}'.format(sstr(s.args[1], sympy_integers=True))
        return result, constraints
    else:
        return sstr(s, sympy_integers=True), ''

def downvalues_rules(r):
    '''
    Function which generates parsed rules by substituting all possible
    combinations of default values.
    '''
    res = []
    parsed = '''
from sympy.external import import_module
matchpy = import_module("matchpy")
from sympy.utilities.decorator import doctest_depends_on

if matchpy:
    from matchpy import Pattern, ReplacementRule, CustomConstraint
    from sympy.integrals.rubi.utility_function import (sympy_op_factory, Int, Set, With, Module, Scan, MapAnd, FalseQ, ZeroQ, NegativeQ, NonzeroQ, FreeQ, NFreeQ, List, Log, PositiveQ, PositiveIntegerQ, NegativeIntegerQ, IntegerQ, IntegersQ, ComplexNumberQ, PureComplexNumberQ, RealNumericQ, PositiveOrZeroQ, NegativeOrZeroQ, FractionOrNegativeQ, NegQ, Equal, Unequal, IntPart, FracPart, RationalQ, ProductQ, SumQ, NonsumQ, Subst, First, Rest, SqrtNumberQ, SqrtNumberSumQ, LinearQ, Sqrt, ArcCosh, Coefficient, Denominator, Hypergeometric2F1, Not, Simplify, FractionalPart, IntegerPart, AppellF1, EllipticPi, EllipticE, EllipticF, ArcTan, ArcCot, ArcCoth, ArcTanh, ArcSin, ArcSinh, ArcCos, ArcCsc, ArcSec, ArcCsch, ArcSech, Sinh, Tanh, Cosh, Sech, Csch, Coth, LessEqual, Less, Greater, GreaterEqual, FractionQ, IntLinearcQ, Expand, IndependentQ, PowerQ, IntegerPowerQ, PositiveIntegerPowerQ, FractionalPowerQ, AtomQ, ExpQ, LogQ, Head, MemberQ, TrigQ, SinQ, CosQ, TanQ, CotQ, SecQ, CscQ, Sin, Cos, Tan, Cot, Sec, Csc, HyperbolicQ, SinhQ, CoshQ, TanhQ, CothQ, SechQ, CschQ, InverseTrigQ, SinCosQ, SinhCoshQ, LeafCount, Numerator, NumberQ, NumericQ, Length, ListQ, Im, Re, InverseHyperbolicQ, InverseFunctionQ, TrigHyperbolicFreeQ, InverseFunctionFreeQ, RealQ, EqQ, FractionalPowerFreeQ, ComplexFreeQ, PolynomialQ, FactorSquareFree, PowerOfLinearQ, Exponent, QuadraticQ, LinearPairQ, BinomialParts, TrinomialParts, PolyQ, EvenQ, OddQ, PerfectSquareQ, NiceSqrtAuxQ, NiceSqrtQ, Together, PosAux, PosQ, CoefficientList, ReplaceAll, ExpandLinearProduct, GCD, ContentFactor, NumericFactor, NonnumericFactors, MakeAssocList, GensymSubst, KernelSubst, ExpandExpression, Apart, SmartApart, MatchQ, PolynomialQuotientRemainder, FreeFactors, NonfreeFactors, RemoveContentAux, RemoveContent, FreeTerms, NonfreeTerms, ExpandAlgebraicFunction, CollectReciprocals, ExpandCleanup, AlgebraicFunctionQ, Coeff, LeadTerm, RemainingTerms, LeadFactor, RemainingFactors, LeadBase, LeadDegree, Numer, Denom, hypergeom, Expon, MergeMonomials, PolynomialDivide, BinomialQ, TrinomialQ, GeneralizedBinomialQ, GeneralizedTrinomialQ, FactorSquareFreeList, PerfectPowerTest, SquareFreeFactorTest, RationalFunctionQ, RationalFunctionFactors, NonrationalFunctionFactors, Reverse, RationalFunctionExponents, RationalFunctionExpand, ExpandIntegrand, SimplerQ, SimplerSqrtQ, SumSimplerQ, BinomialDegree, TrinomialDegree, CancelCommonFactors, SimplerIntegrandQ, GeneralizedBinomialDegree, GeneralizedBinomialParts, GeneralizedTrinomialDegree, GeneralizedTrinomialParts, MonomialQ, MonomialSumQ, MinimumMonomialExponent, MonomialExponent, LinearMatchQ, PowerOfLinearMatchQ, QuadraticMatchQ, CubicMatchQ, BinomialMatchQ, TrinomialMatchQ, GeneralizedBinomialMatchQ, GeneralizedTrinomialMatchQ, QuotientOfLinearsMatchQ, PolynomialTermQ, PolynomialTerms, NonpolynomialTerms, PseudoBinomialParts, NormalizePseudoBinomial, PseudoBinomialPairQ, PseudoBinomialQ, PolynomialGCD, PolyGCD, AlgebraicFunctionFactors, NonalgebraicFunctionFactors, QuotientOfLinearsP, QuotientOfLinearsParts, QuotientOfLinearsQ, Flatten, Sort, AbsurdNumberQ, AbsurdNumberFactors, NonabsurdNumberFactors, SumSimplerAuxQ, Prepend, Drop, CombineExponents, FactorInteger, FactorAbsurdNumber, SubstForInverseFunction, SubstForFractionalPower, SubstForFractionalPowerOfQuotientOfLinears, FractionalPowerOfQuotientOfLinears, SubstForFractionalPowerQ, SubstForFractionalPowerAuxQ, FractionalPowerOfSquareQ, FractionalPowerSubexpressionQ, Apply, FactorNumericGcd, MergeableFactorQ, MergeFactor, MergeFactors, TrigSimplifyQ, TrigSimplify, TrigSimplifyRecur, Order, FactorOrder, Smallest, OrderedQ, MinimumDegree, PositiveFactors, Sign, NonpositiveFactors, PolynomialInAuxQ, PolynomialInQ, ExponentInAux, ExponentIn, PolynomialInSubstAux, PolynomialInSubst, Distrib, DistributeDegree, FunctionOfPower, DivideDegreesOfFactors, MonomialFactor, FullSimplify, FunctionOfLinearSubst, FunctionOfLinear, NormalizeIntegrand, NormalizeIntegrandAux, NormalizeIntegrandFactor, NormalizeIntegrandFactorBase, NormalizeTogether, NormalizeLeadTermSigns, AbsorbMinusSign, NormalizeSumFactors, SignOfFactor, NormalizePowerOfLinear, SimplifyIntegrand, SimplifyTerm, TogetherSimplify, SmartSimplify, SubstForExpn, ExpandToSum, UnifySum, UnifyTerms, UnifyTerm, CalculusQ, FunctionOfInverseLinear, PureFunctionOfSinhQ, PureFunctionOfTanhQ, PureFunctionOfCoshQ, IntegerQuotientQ, OddQuotientQ, EvenQuotientQ, FindTrigFactor, FunctionOfSinhQ, FunctionOfCoshQ, OddHyperbolicPowerQ, FunctionOfTanhQ, FunctionOfTanhWeight, FunctionOfHyperbolicQ, SmartNumerator, SmartDenominator, SubstForAux, ActivateTrig, ExpandTrig, TrigExpand, SubstForTrig, SubstForHyperbolic, InertTrigFreeQ, LCM, SubstForFractionalPowerOfLinear, FractionalPowerOfLinear, InverseFunctionOfLinear, InertTrigQ, InertReciprocalQ, DeactivateTrig, FixInertTrigFunction, DeactivateTrigAux, PowerOfInertTrigSumQ, PiecewiseLinearQ, KnownTrigIntegrandQ, KnownSineIntegrandQ, KnownTangentIntegrandQ, KnownCotangentIntegrandQ, KnownSecantIntegrandQ, TryPureTanSubst, TryTanhSubst, TryPureTanhSubst, AbsurdNumberGCD, AbsurdNumberGCDList, ExpandTrigExpand, ExpandTrigReduce, ExpandTrigReduceAux, NormalizeTrig, TrigToExp, ExpandTrigToExp, TrigReduce, FunctionOfTrig, AlgebraicTrigFunctionQ, FunctionOfHyperbolic, FunctionOfQ, FunctionOfExpnQ, PureFunctionOfSinQ, PureFunctionOfCosQ, PureFunctionOfTanQ, PureFunctionOfCotQ, FunctionOfCosQ, FunctionOfSinQ, OddTrigPowerQ, FunctionOfTanQ, FunctionOfTanWeight, FunctionOfTrigQ, FunctionOfDensePolynomialsQ, FunctionOfLog, PowerVariableExpn, PowerVariableDegree, PowerVariableSubst, EulerIntegrandQ, FunctionOfSquareRootOfQuadratic, SquareRootOfQuadraticSubst, Divides, EasyDQ, ProductOfLinearPowersQ, Rt, NthRoot, AtomBaseQ, SumBaseQ, NegSumBaseQ, AllNegTermQ, SomeNegTermQ, TrigSquareQ, RtAux, TrigSquare, IntSum, IntTerm, Map2, ConstantFactor, SameQ, ReplacePart, CommonFactors, MostMainFactorPosition, FunctionOfExponentialQ, FunctionOfExponential, FunctionOfExponentialFunction, FunctionOfExponentialFunctionAux, FunctionOfExponentialTest, FunctionOfExponentialTestAux, stdev, rubi_test, If, IntQuadraticQ, IntBinomialQ, RectifyTangent, RectifyCotangent, Inequality, Condition, Simp, SimpHelp, SplitProduct, SplitSum, SubstFor, SubstForAux, FresnelS, FresnelC, Erfc, Erfi, Gamma, FunctionOfTrigOfLinearQ, ElementaryFunctionQ, Complex, UnsameQ, _SimpFixFactor, SimpFixFactor, _FixSimplify, FixSimplify, _SimplifyAntiderivativeSum, SimplifyAntiderivativeSum, _SimplifyAntiderivative, SimplifyAntiderivative, _TrigSimplifyAux, TrigSimplifyAux, Cancel, Part, PolyLog, D, Dist)
    from sympy import Integral, S, sqrt
    from sympy.integrals.rubi.symbol import WC
    from sympy.core.symbol import symbols
    from sympy.functions import (log, sin, cos, tan, cot, csc, sec, sqrt, erf, exp, log)
    from sympy.functions.elementary.hyperbolic import (acosh, asinh, atanh, acoth, acsch, asech, cosh, sinh, tanh, coth, sech, csch)
    from sympy.functions.elementary.trigonometric import (atan, acsc, asin, acot, acos, asec)

    A_, B_, C_, F_, G_, H_, a_, b_, c_, d_, e_, f_, g_, h_, i_, j_, k_, l_, m_, n_, p_, q_, r_, t_, u_, v_, s_, w_, x_, y_, z_ = [WC(i) for i in 'ABCFGHabcdefghijklmnpqrtuvswxyz']
    a1_, a2_, b1_, b2_, c1_, c2_, d1_, d2_, n1_, n2_, e1_, e2_, f1_, f2_, g1_, g2_, n1_, n2_, n3_, Pq_, Pm_, Px_, Qm_, Qr_, Qx_, jn_, mn_, non2_, RFx_, RGx_ = [WC(i) for i in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'd1', 'd2', 'n1', 'n2', 'e1', 'e2', 'f1', 'f2', 'g1', 'g2', 'n1', 'n2', 'n3', 'Pq', 'Pm', 'Px', 'Qm', 'Qr', 'Qx', 'jn', 'mn', 'non2', 'RFx', 'RGx']]

    _UseGamma = False

def rubi_object(rubi):

'''
    #d, p, q, r, s, v, mn, gcd, P, Q, lst = symbols('d p q r s v mn gcd P Q lst')

    index = 0
    for i in r:
        print('parsing rule {}'.format(r.index(i) + 1))
        # Parse Pattern
        if i[1][1][0] == 'Condition':
            p = i[1][1][1].copy()
        else:
            p = i[1][1].copy()

        optional = get_default_values(p, {})
        pattern = generate_sympy_from_parsed(p.copy(), replace_Int=True)
        pattern, free_symbols = add_wildcards(pattern, optional=optional)
        free_symbols = list(set(free_symbols)) #remove common symbols

        # Parse Transformed Expression and Constraints
        if i[2][0] == 'Condition': # parse rules without constraints seperately
            constriant = divide_constraint(i[2][2], free_symbols) # seperate And constraints into indivdual constraints
            FreeQ_vars, FreeQ_x = seperate_freeq(i[2][2].copy()) # seperate FreeQ into indivdual constraints
            transformed = generate_sympy_from_parsed(i[2][1].copy(), symbols=free_symbols)
        else:
            constriant = ''
            FreeQ_vars, FreeQ_x = [], []
            transformed = generate_sympy_from_parsed(i[2].copy(), symbols=free_symbols)

        FreeQ_constraint = parse_freeq(FreeQ_vars, FreeQ_x, free_symbols)
        pattern = sympify(pattern)
        pattern = sstr(pattern, sympy_integers=True)
        pattern = setWC(pattern)
        transformed = sympify(transformed)

        index += 1
        if type(transformed) == Function('With') or type(transformed) == Function('Module'):
            transformed, With_constraints = setWith(transformed, free_symbols, index)
            parsed += '    pattern' + str(index) +' = Pattern(' + pattern + '' + FreeQ_constraint + '' + constriant + With_constraints + ')'
            parsed += '\n{}'.format(transformed)
            parsed += '\n    ' + 'rule' + str(index) +' = ReplacementRule(' + 'pattern' + sstr(index, sympy_integers=True) + ', lambda ' + ', '.join(free_symbols) + ' : ' + 'With{}({})'.format(index, ', '.join(free_symbols)) + ')\n    '
        else:
            transformed = sstr(transformed, sympy_integers=True)
            parsed += '    pattern' + str(index) +' = Pattern(' + pattern + '' + FreeQ_constraint + '' + constriant + ')'
            parsed += '\n    ' + 'rule' + str(index) +' = ReplacementRule(' + 'pattern' + sstr(index, sympy_integers=True) + ', lambda ' + ', '.join(free_symbols) + ' : ' + transformed + ')\n    '
        parsed += 'rubi.add(rule'+ str(index) +')\n\n'

    parsed += '    return rubi\n'

    return parsed

with open('downvalues.txt','r') as f_open:
    full_string = f_open.read()

for i in temporary_variable_replacement:
    full_string = full_string.replace(i, temporary_variable_replacement[i])

for i in permanent_variable_replacement:
    full_string = full_string.replace(i, permanent_variable_replacement[i])

res = parse_full_form(full_string)
rules = []

for i in res: # separate all rules
    if i[0] == 'RuleDelayed':
        rules.append(i)

result = downvalues_rules(rules)

for i in temporary_variable_replacement:
    result = result.replace(temporary_variable_replacement[i], i)

result = result.strip()
result += '\n'

f = open("patterns.py","w")
f.write(result)
f.close()
