# this is a teset implementation of a graphing thing

import shutil, sympy, math
from sympy.parsing.sympy_parser import standard_transformations, parse_expr, implicit_multiplication_application

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

print(render_fn("y = sin(x)"))