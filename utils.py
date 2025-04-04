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

# arbitrary precision arithmetic fraction class
# TODO: rename vars to be clearer, add some other utilities.
# maybe use `Component` to represent rationals, roots, imaginary nums and imaginary roots.
class Fraction:
    # todo: get from string and list representations and float
    def __init__(self, num, den):
        if num * den < 0:
            self.num = -abs(num)
            self.den = abs(den)
        elif num * den > 0:
            self.num = abs(num)
            self.den = abs(den)
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
    def __init__(self, mag: str | int | float, dir: str | int | float, mode = "rad"):
        self.mag = parse_num(str(mag))
        self.dir = parse_num(str(dir))
        self.__fix_angle__()
        self.mode = mode

    def add(self, other: Vector):
        pass

    def subtract(self, other: Vector):
        pass

    def multiply(self, other: Vector):
        pass

    def convert(self, mode = "rad"):
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
