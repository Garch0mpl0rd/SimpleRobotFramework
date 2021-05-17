from yaml import safe_load


def load(filename, key):
    with open(filename) as f:
        result = safe_load(f)
    return result[key]

