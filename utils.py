# utility file for modules
# ignore_module
import math, sympy, shutil
from sympy.parsing.sympy_parser import standard_transformations, parse_expr, implicit_multiplication_application

PI = math.pi
RAD2DEG = 180 / PI
# parse num util function
def parse_num(num: str):
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return num


def get_valid_fraction(msg="", sentinel="exit"):
    while True:
        try:
            inp = input(msg)
            if inp == sentinel:
                return "exit"
            return Fraction(inp)
        except Exception:
            print("Invalid input. Please try again")


# do NOT touch this, you will fuck everything up
# clamps the input angle to within the acceptable range
# angle => (0, 360) if degrees
# angle => (0, 2PI) if radians
def clamp_angle(angle, radians=True):
    return ((1 - 2 * int(abs(angle) != angle)) * (abs(angle) % [360, 2 * PI][int(radians)]) + 2 * [360, PI][int(radians)]) % [360, PI][int(radians)]


def rounded_str(num: float, precision: int=3):
    rnd = round(num, precision)
    if rnd.is_integer():
        rnd = int(rnd)
    return str(rnd)


def signstr(num: float | int):
    return ("-" if abs(num) != num else "+") + str(abs(num))


# arbitrary precision arithmetic fraction class
# todo: clean up this class (never nester technique)
class Fraction:
    def __init__(self, num, den=None):
        if den and parse_num(den) == 0:
            raise ValueError("A Fraction cannot have a denomerator of 0.")
        if type(num) is int:
            self.num = num
            self.den = den if den else 1
        elif type(num) is float:
            if den:
                frac = Fraction(num) / Fraction(den)
                self.num = frac.num
                self.den = frac.den

            whole, decimal = math.floor(num), num % 1
            factor = 10**len(str(decimal)[2:])
            self.num = int(whole * factor + decimal * factor)
            self.den = factor
        elif type(num) is str:
            if num.count("-") > 1 and num.count("/") == 0:
                raise ValueError(f"Cannot create a Fraction from {num}{f'and {den}' if den else ''}")
            if den and den.count("-") > 1 and den.count("/") == 0:
                raise ValueError(f"Cannot create a Fraction from {num} and {den}")
            if den:
                frac = Fraction(num) / Fraction(den)
                self.num = frac.num
                self.den = frac.den
            else:
                # todo: shit doesnt parse a negative correctly
                if num.count(".") == 1 and num.count("/") == 0:  # float string
                    # slice the string into the respective chunks (whole.fraction)
                    float_parts = num.split(".")
                    sign = 1
                    whole = 0
                    if len(float_parts[0]) > 0:
                        if float_parts[0][0] == "-":
                            sign = -1
                            float_parts[0] = float_parts[0][1:]
                        whole = int(float_parts[0])
                    
                    # determine the denomerator from the fraction digit count
                    factor = 10**len(float_parts[1])
                    # process the two parts accordingly 
                    self.num = whole * factor + int(float_parts[1])
                    self.den = factor * sign
                elif num.count(".") > 1 and num.count("/") == 0:
                    raise ValueError(f"Cannot create a fraction from {num}")
                else:
                    frac = parse_num(num.lstrip().rstrip())
                    if type(frac) is not str:
                        new_frac = Fraction(frac)
                        self.num = new_frac.num
                        self.den = new_frac.den
                    else:  # assume it is a mixed number
                        extra_chars = frac.strip("0123456789/-. ")
                        if len(extra_chars) > 0 or frac.count("/") > 1:  # if there are any extra characters, it is not a valid fraction
                            raise ValueError(f"Unable to create a Fraction from {frac}; it is not a valid fraction.")
                        
                        # remove all empty strings
                        parts = [p for p in frac.split(" ") if p != ""]
                        if len(parts) > 1 and "/" in parts[1]:  # detect properly formatted fraction and skip
                            pass
                        elif "/" not in parts[0] and "/" not in parts[1]:
                            if "/" not in parts[-1]:
                                parts[1] = "".join(parts[1:])
                                parts = parts[:2]
                        else:
                            parts = ["".join(parts)]

                        # these are some final if statements to format the parts
                        # could be cleaned up with refactoring
                        if len(parts) == 3:
                            if parts[1].endswith("/") or parts[2].startswith('/'):
                                parts = [parts[0], "".join(parts[1:])]
                        if len(parts) == 2 and parts[1].startswith("/") or parts[0].endswith('/'):
                            the_part = "".join(parts)
                            parts = [the_part]
                        
                        # parts should be ['a/b'] or ['a', 'b/c']
                        if len(parts) == 2:  # mixed fraction (a b/c)
                            improper = [int(n) for n in parts[1].split("/")]
                            denom = improper[1]
                            # properly accepts a negative mixed fraction (-a b/c is assumed to be all negative)
                            if abs(int(parts[0])) != int(parts[0]):
                                improper[0] *= -1
                            frac = Fraction(int(parts[0]) * denom + improper[0], denom)
                            self.num = frac.num
                            self.den = frac.den
                        elif len(parts) == 1:  # improper fraction (a/b)
                            frac = Fraction(*parts[0].split("/"))
                            self.num = frac.num
                            self.den = frac.den
        elif type(num) is list:
            if den:
                raise ValueError(f"Unable to create a Fraction from two lists; only one is required.")
            # can't set self to the new fraction for some reason
            if len(num) > 2:
                raise ValueError("Cannot create a Fraction from a list with more than 2 elements.")
            frac = Fraction(*num)
            self.num = frac.num
            self.den = frac.den
        else:
            raise ValueError(f"Cannot create a Fraction from {num} and {den}")

        if (self.num < 0) ^ (self.den < 0):
            self.num = -abs(self.num)
            self.den = abs(self.den)
        else:
            self.num = abs(self.num)
            self.den = abs(self.den)

        if self.den == 0 and self.num != 0:
            raise ValueError("A Fraction's denomerator cannot be zero.")
        self.simplify()

    def simplify(self):
        if self.den == 0:
            raise ValueError("A Fraction cannot have a denomenator of 0")
        greatest_factor = math.gcd(self.num, self.den)
        self.num = self.num // greatest_factor
        self.den = self.den // greatest_factor

    def __add__(self, other):
        a, b, c, d = self.num, self.den, other.num, other.den
        denom = math.lcm(b, d)
        f1, f2 = denom // b, denom // d
        return Fraction(a * f1 + c * f2, denom)

    def __sub__(self, other):
        return self + Fraction(other.num * -1, other.den)

    def __mul__(self, other):
        if type(other) is int:
            return Fraction(self.num * other, self.den)
        if type(other) is float:
            return Fraction(other) * self

        if type(other) is Fraction:
            return Fraction(self.num * other.num, self.den * other.den)
        else:  # if not multiplying by a number,
            return

    
    def __truediv__(self, other):
        if type(other) is int:
            return Fraction(self.num, self.den * other)
        if type(other) is float:
            divisor = Fraction(other)
            return Fraction(self.num * divisor.den, self.den * divisor.num)

        if type(other) is Fraction:
            return Fraction(self.num * other.den, self.den * other.num)
        else:  # if not multiplying by a number,
            return

    def __str__(self):
        return f"{self.num}/{self.den}"


# radius: radius of vector, interpreted as x if polar = False
# angle: angle of vector, interepreted as y in polar = True
# polar: polar or cartesian?
# radians: radians or degrees?
class Vector:
    def __init__(self, radius: float | int, angle: float | int, polar: bool=False, radians: bool=True):
        self.polar = polar
        self.radians = radians
        if polar:
            self.radius = float(radius)
            self.angle = clamp_angle(float(angle), radians)
            if abs(self.radius) != self.radius:
                self.radius = abs(self.radius)
                self.angle += PI if self.radians else 180
        else:
            self.x = float(radius)
            self.y = float(angle)
        

    def __add__(self, other):
        radians = self.radians or other.radians
        polar = self.polar and other.polar

        self.to_cartesian()
        other.to_cartesian()

        added = Vector(self.x + other.x, self.y + other.y)

        if polar:
            added.to_polar()
        if radians:
            added.to_radians()

        return added

    def __sub__(self, other):
        radians = self.radians or other.radians
        polar = self.polar and other.polar

        self.to_cartesian()
        other.to_cartesian()

        added = Vector(self.x - other.x, self.y - other.y)

        if polar:
            added.to_polar()
        if radians:
            added.to_radians()

        return added

    def __str__(self):
        if self.polar:
            return f"{rounded_str(self.radius)}∠ {rounded_str(self.angle)}"
        else:
            return f"{rounded_str(self.x)}î {signstr(round(self.y, 3))}ĵ"

    def to_polar(self):
        if self.polar:
            return

        self.radius = math.sqrt(self.x * self.x + self.y * self.y)  
        rho = math.atan(abs(self.y / self.x)) if self.x != 0 else 0 # in radians

        axes = [self.x >= 0, self.y >= 0]

        if all(axes):  # Q1
            self.angle = rho
        elif axes[1]:  # Q2
            self.angle = PI - rho
        elif not any(axes): # Q3
            self.angle = PI + rho
        else:  # Q4
            self.angle = 2 * PI - rho
        if not self.radians:
            self.to_degrees()

        self.polar = True


    def to_cartesian(self):
        if not self.polar:
            return
        
        mult = 1 if self.radians else RAD2DEG
        self.x = self.radius * math.cos(self.angle * mult)
        self.y = self.radius * math.sin(self.angle * mult)

        self.polar = False

    def to_radians(self):
        if not self.polar or self.radians:
            return
        
        self.angle *= RAD2DEG
        self.radians = True

    def to_degrees(self):
        if not self.polar or not self.radians:
            return
        
        self.angle /= RAD2DEG
        self.radians = False

    def print_state(self):
        try:
            rad = self.radius
            rstr = "radius"
        except Exception:
            rad = self.x
            rstr = "x"

        try:
            ang = str(self.angle)
            if not self.radians:
                ang += "°"
            astr = "angle"
        except Exception:
            ang = self.y
            astr = "y"
        infostr = f"""
        {rstr}: {rad}
        {astr}: {ang}
        polar: {self.polar}
        radians: {self.radians}
        """

        print(infostr)


X_OFFSET = 9 / 87
Y_OFFSET_SMALL = 8 / 87
Y_OFFSET_LARGE = 24 / 87

# bits: length-8 array of int/bool where this is the bit order:
# 0 4
# 1 5
# 2 6
# 3 7
def braille_from_bits(bits: list[int]):
    transformed = [
        bits[0], bits[1],
        bits[2], bits[4],
        bits[5], bits[6], 
        bits[3], bits[7]
    ]
    
    return chr(0x2800 + sum(b << i for (i, b) in enumerate(transformed)))

def get_rel_from_eq(eqstr: str):
    eqstr = eqstr.replace("^", "**")
    if "=" in eqstr:
        lhs, rhs = eqstr.split("=")
        expr = f"{lhs}-({rhs})"
    else:
        expr = f"{eqstr} - y"
        
    transformations = standard_transformations + (implicit_multiplication_application, )
    relation = sympy.parse_expr(expr, transformations=transformations)
    
    return sympy.lambdify(sympy.symbols("x y"), relation, "numpy")

def fill_buffer(xstep, ystep, camera, size, relation_fns):
    x_off = xstep * X_OFFSET
    y_off_s = -ystep * Y_OFFSET_SMALL
    y_off_l = -ystep * Y_OFFSET_LARGE
    
    # buffer structure
    # [ [ [8 braille segments] for each char in row ] for each row ]
    buffer = [
        [[0, 0, 0, 0, 0, 0, 0, 0] for _ in range(size[0])] for _ in range(size[1]) 
    ]
    
    lerp = lambda range, t: range[0] + t * (range[1] - range[0])
    
    for fn, fn_epsilon in relation_fns:
        for y_idx in range(size[1]):
            for x_idx in range(size[0]):
                # center of char
                x = lerp(camera["horizontal"], x_idx / size[0])
                y = -lerp(camera["vertical"], y_idx / size[1])
                
                buffer[y_idx][x_idx] = [min(x + y, 1) for (x, y) in zip(buffer[y_idx][x_idx], [
                    int(abs(fn(x - x_off, y - y_off_l)) <= fn_epsilon),
                    int(abs(fn(x - x_off, y - y_off_s)) <= fn_epsilon),
                    int(abs(fn(x - x_off, y + y_off_s)) <= fn_epsilon),
                    int(abs(fn(x - x_off, y + y_off_l)) <= fn_epsilon),
                    int(abs(fn(x + x_off, y - y_off_l)) <= fn_epsilon),
                    int(abs(fn(x + x_off, y - y_off_s)) <= fn_epsilon),
                    int(abs(fn(x + x_off, y + y_off_s)) <= fn_epsilon),
                    int(abs(fn(x + x_off, y + y_off_l)) <= fn_epsilon),
                ])]
                
    return buffer

# eq_str: either an equation string or list of them
# size: size of output buffer in chars
# with_axes: whether to render axes
# epsilon: treshold for rendering plot. the higher it is, the more points will be drawn. 
# too high of a value may obscure the actual shape of the plot.
# camera: camera bound settings; horizontal for maximal horizontal
def render_fn(eq_str: str | list[str], size=shutil.get_terminal_size(), with_axes=True, epsilon=None, camera = {
    "horizontal": [-10, 10],
    "vertical": [-10, 10]
}):
    xstep = (camera["horizontal"][1] - camera["horizontal"][0]) / size[0] 
    ystep = (camera["vertical"][1] - camera["vertical"][0]) / size[1] 
    
    autoepsilon = 0.5 * math.hypot(xstep, ystep)
    epsilon = autoepsilon if epsilon is None else epsilon
    
    fns_list = [(eq_str, epsilon)] if type(eq_str) is not list else [(eq, epsilon) for eq in eq_str]
    if with_axes:
        fns_list.extend([("x = 0", autoepsilon / 2), ("y = 0", autoepsilon / 2)])
        pass
    relation_fns = [(get_rel_from_eq(fn), epsilon) for fn, epsilon in fns_list]
    
    buffer = fill_buffer(xstep, ystep, camera, size, relation_fns)

    return "\n".join(["".join([braille_from_bits(char) for char in buf_row]) for buf_row in buffer])