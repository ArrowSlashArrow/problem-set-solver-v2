import sympy, functools, math, utils, random

from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, rationalize

transformations = (standard_transformations + (implicit_multiplication_application, rationalize,))

remove_symbols = ["*"]
def eq_str(eq, subs_dict={}):
    eq_string = f"{eq.lhs} = {eq.rhs}"
    for symbol, sub in subs_dict.items():
        eq_string = eq_string.replace(f"{symbol}", f"({sub})")
        
    for symbol in remove_symbols:
        eq_string = eq_string.replace(symbol, "")

    return eq_string

def get_eq(eq_str, implied_rhs=""):
    replaced = eq_str.replace("exp", "e^").replace("^", "**").replace("e", "2.718281828").replace("pi", "3.14159265358979") + implied_rhs
    lhs, rhs = replaced.split("=")
    lhs_expr = parse_expr(lhs.strip(), transformations=transformations)
    rhs_expr = parse_expr(rhs.strip(), transformations=transformations)
    return sympy.Eq(lhs_expr, rhs_expr)

eqstrs = [
    # "2x + y + z = 9",
    # "x + 3y + 2z = 17",
    # "x = 2z",
    
    # x = 8/3; y = 5/3
    # "2x + y = 7",
    # "x - y = 1",

    # x = 18/5; y = 18/5
    "3x + 2y = 18",
    "x - y = 1",

    # x = 8/3; y = 11/3
    # "4x - y = 7",
    # "2x + y = 9",
    
    # "0.5(x) + 0.8(100) = 0.9(x + 100)"
]


def get_symbols_from_eqs(eq_strs):
    eqs = [get_eq(eq) for eq in eq_strs]
    symbols = set()
    for eq in eqs:
        symbols.update(eq.free_symbols)

    available_eqs = eqs
    used_eqs = {}  # {x: 2y + 5, y: ..., ...}
    # substituions for all vars in all equations
    for symbol in symbols:
        prev_score = 9999.0
        prev_eq = None
        for eq in available_eqs:
            solved = sympy.solve(eq, symbol)[0]
            denoms = [v.q for _, v in solved.as_coefficients_dict().items()]
            max_coef = max(denoms)
            gcd = functools.reduce(math.gcd, denoms)
            denoms = [d / gcd for d in denoms]
            score = max_coef * math.prod(denoms)  # the lower the better
            
            # print(f"{symbol} = {solved}; coef rating of {score}")
            if score < prev_score:
                prev_score = score
                prev_eq = eq
                
        # print(f"easiest equation to work with for {symbol}: {eq_str(prev_eq)}\n")
        used_eqs[symbol] = prev_eq
        available_eqs.remove(prev_eq)
    
    return used_eqs

            
def solve_eq_system(eqstrs):
    solutions = {}
    steps = []  # array of array of strings: each inner array is a section

    used_eqs_as_list = list(get_symbols_from_eqs(eqstrs).items())
    # sometimes the equations are in such an order that a solution is impossible
    # this is used to mitigate that
    random.shuffle(used_eqs_as_list)
    steps.append([eq_str(eq) for _, eq in used_eqs_as_list])

    # btw this is substitution
    # TODO: general form for any amount of vars. too lazy to do that rn
    match len(used_eqs_as_list):
        case 2:
            s1, eq1 = used_eqs_as_list[0]
            s2, eq2 = used_eqs_as_list[1]
            
            isolation_steps = []
            substitution_steps = []
            
            # solve normally for a value for one variable
            first_solved = sympy.solve(eq1, s1)[0]
            isolation_steps.append(eq_str(sympy.Eq(s1, first_solved)))
            
            second_substituted = eq2.subs({s1: first_solved})
            isolation_steps.append(eq_str(eq2, {s1: first_solved}))
            isolation_steps.append(eq_str(second_substituted))
            
            # solutions
            
            second_solved = sympy.solve(second_substituted, s2)[0]
            solutions[s2] = second_solved
            
            # backpropagate solved equation to first var
            first_backpropagated = first_solved.subs({s2: second_solved})
            solutions[s1] = first_backpropagated
            
            steps.extend([isolation_steps, substitution_steps])
            
        case 3:
            s1, eq1 = used_eqs_as_list[0]
            s2, eq2 = used_eqs_as_list[1]
            s3, eq3 = used_eqs_as_list[2]
            
            isolation_steps = []
            substitution_steps = []

            # s1 = ...
            first_solved = sympy.solve(eq1, s1)[0]
            isolation_steps.append(eq_str(sympy.Eq(s1, first_solved)))
            
            isolation_steps.append(eq_str(eq2, {s1: first_solved}))
            second_substituted = eq2.subs({s1: first_solved})
            isolation_steps.append(eq_str(second_substituted))
            
            # s2 = ...
            second_solved = sympy.solve(second_substituted, s2)[0]
            isolation_steps.append(eq_str(sympy.Eq(s2, second_solved)))
            
            # s1 = ... (resubstituted)
            substitution_steps.append(eq_str(sympy.Eq(s1, first_solved), {s2: second_solved}))
            first_solved = first_solved.subs({s2: second_solved})
            substitution_steps.append(eq_str(sympy.Eq(s1, first_solved)))
            
            # solutions start here
            
            substitution_steps.append(eq_str(eq3, {s1: first_solved, s2: second_solved}))
            third_solved = sympy.solve(eq3.subs({s1: first_solved, s2: second_solved}), s3)[0]
            solutions[s3] = third_solved
            
            # below: all substitutions for last symbol in previous equations.
            # the last symbol is all that remains after the equations were all resubbed
            
            # s2 = ... (resubstituted)
            second_solved = second_solved.subs({s3: third_solved})
            solutions[s2] = second_solved
            
            # s1 = ... (resubstituted again)
            first_solved = first_solved.subs({s3: third_solved})
            solutions[s1] = first_solved
            
            steps.extend([isolation_steps, substitution_steps])
        
        case _:
            steps.append(["im working on it"])

    
    solutions_as_list = list(solutions.items())
    solutions_as_list.sort(key= lambda element: f"{element[0]}")
    solutions = []
    for symbol, solution in solutions_as_list:
        solutions.append(f"{symbol} = {solution}")
        
    steps.append(solutions)
    return steps

def _eq_solve_handler(eqstrs, attempt_limit=10):
    attempts = 0
    while attempts < attempt_limit:
        try:
            attempts += 1
            return solve_eq_system(eqstrs)
        except:
            pass
    return []

def display_steps(steps):
    for section in steps:
        for step in section:
            print(step)
        print()
        
def solve_eq_system_with_steps(eqstrs):
    display_steps(_eq_solve_handler(eqstrs))

solve_eq_system_with_steps(eqstrs)
print(utils.render_plot(eqstrs, size=[80, 40]))