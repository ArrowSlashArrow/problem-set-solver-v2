# utility file for modules
# ignore_module
import sympy, math


# parse num util function
def parse_num(num: str):
    try:
        return int(num)
    except ValueError:
        try:
            return float(num)
        except ValueError:
            return num


def get_valid_fraction(msg):
    while True:
        try:
            return Fraction(input(msg))
        except Exception:
            print("Invalid input. Please try again")


# arbitrary precision arithmetic fraction class
# todo: clean up this class (never nester technique)
class Fraction:
    def __init__(self, num, den=None):
        if type(num) is int:
            self.num = num
            self.den = den if den else 1
        elif type(num) is float:
            if den:
                raise ValueError(f"Unable to create a Fraction from two floats; only one is required.")

            whole, decimal = math.floor(num), num % 1
            factor = 10**len(str(decimal)[2:])
            self.num = int(whole * factor + decimal * factor)
            self.den = factor
        elif type(num) is str:
            if den:
                frac = Fraction(num) / Fraction(den)
                self.num = frac.num
                self.den = frac.den
            else:
                frac = parse_num(num.lstrip().rstrip())
                if type(frac) is not str:
                    new_frac = Fraction(frac)
                    self.num = new_frac.num
                    self.den = new_frac.den
                else:  # assume it is a mixed number
                    extra_chars = frac.strip("0123456789/ ")
                    if len(extra_chars) > 0 or frac.count("/") > 1:  # if there are any extra characters, it is not a valid fraction
                        raise ValueError(f"Unable to create a Fraction from {frac}; it is not a valid fraction.")

                    # remove all empty strings
                    parts = [p for p in frac.split(" ") if p != ""]
                    if "/" not in parts[0] and "/" not in parts[1]:
                        if "/" not in parts[-1]:
                            parts[1] = "".join(parts[1:])
                            parts = parts[:2]
                    else:
                        parts = ["".join(parts)]
                    
                    # parts should be ['a/b'] or ['a', 'b/c']
                    if len(parts) == 2:  # mixed fraction (a b/c)
                        parts[1] = "".join(parts[1:])
                        improper = [int(n) for n in parts[1].split("/")]
                        denom = improper[1]
                        frac = Fraction(
                            int(parts[0]) * denom + improper[0], denom)
                        self.num = frac.num
                        self.den = frac.den
                    elif len(parts) == 1:  # improper fraction (a/b)
                    
                        frac = Fraction(parts[0].split("/"))
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

        if self.num * self.den < 0:
            self.num = -abs(self.num)
            self.den = abs(self.den)
        elif self.num * self.den > 0:
            self.num = abs(self.num)
            self.den = abs(self.den)
        else:
            self.num = 0
            self.den = 0

        self.simplify()

    def simplify(self):
        g = math.gcd(self.num, self.den)
        self.num = self.num // g
        self.den = self.den // g

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
            pass  # todo: float -> fraction, then multiply

        if type(other) is Fraction:
            return Fraction(self.num * other.num, self.den * other.den)
        else:  # if not multiplying by a number,
            return

    # floordiv doesn't make sense here
    def __truediv__(self, other):
        if type(other) is int:
            return Fraction(self.num, self.den * other)
        if type(other) is float:
            pass  # todo: float -> fraction, then divide

        if type(other) is Fraction:
            return Fraction(self.num * other.den, self.den * other.num)
        else:  # if not multiplying by a number,
            return

    def __str__(self):
        return f"{self.num}/{self.den}"


# mag - magnitude of the vector
# dir - number in radians or degrees (max: 2pi, 360deg)
# mode - "rad" or "deg"
# TODO: set the type of `mag` to be of struct Fraction
# TODO: maybe change internal dir to always be radians and convert as needed? (easier operations)
class Vector:

    def __init__(self,
                 mag: str | int | float,
                 dir: str | int | float,
                 mode="rad"):
        self.mag = parse_num(str(mag))
        self.dir = parse_num(str(dir))
        self.__fix_angle__()
        self.mode = mode

    def add(self, other):
        pass

    def subtract(self, other):
        pass

    def multiply(self, other):
        pass

    def convert(self, mode="rad"):
        if self.mode == mode:
            return False

        if mode == "rad":
            self.dir *= math.pi / 180
        else:
            self.dir *= 180 / math.pi

        return True

    def __fix_angle__(self):
        if self.dir < 0:
            if self.mode == "rad":
                self.dir = math.pi * 2 + self.dir
            else:
                self.dir = 360 + self.dir
            # recurse to make sure it still isn't negative
            return self.__fix_angle__()

        return

    def get_str(self):
        return str(self.mag) + "/" + str(self.dir) + self.mode
