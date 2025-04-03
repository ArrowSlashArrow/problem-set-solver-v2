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
class Number:
    def __init__(self, num: str | int | float):
        numer = 1
        denom = 1
        num = parse_num(str(num))

        if type(num) == float:
            numer = int(num)
            denom = 10 ** len(str(num).split(".")[1])
        elif type(num) == int:
            numer = num
            denom = 1
        else:
            raise ValueError("Invalid input: " + num)
        
        self.numer = numer
        self.denom = denom
    def multiply(other: Number):
        self.numer *= other.numer
        self.denom *= other.denom


# mag - magnitude of the vector
# dir - number in radians or degrees (max: 2pi, 360deg)
# mode - "rad" or "deg"
# TODO: set the type of `mag` to be of struct Number
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
