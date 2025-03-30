# utility file for modules
# ignore_module

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
        