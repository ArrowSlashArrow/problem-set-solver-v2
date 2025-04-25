
# wanted to refactor this but couldn't
# if it works, don't touch it
def pack_dicts(*args):
    keys = [list(arg.keys()) for arg in args]
    if len(set(map(tuple, keys))) != 1:
        return args[0]
    keys = keys[0]
    values = [list(arg.values()) for arg in args]
    vals = list(map(list, zip(*values[::-1])))
    return {k: v for k, v in zip(keys, vals)}