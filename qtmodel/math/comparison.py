import sys


def close(x, y, n: int = 42):
    # Deals with +infinity and -infinity representations etc.
    if x == y:
        return True

    diff = abs(x - y)
    tolerance = n * sys.float_info.epsilon

    if x * y == 0.0:  # x or y = 0.0
        return diff < (tolerance * tolerance)

    return diff <= tolerance * abs(x) and diff <= tolerance * abs(y)


def close_enough(x, y, n: int = 42):
    # Deals with +infinity and -infinity representations etc.
    if x == y:
        return True

    diff = abs(x - y)
    tolerance = n * sys.float_info.epsilon

    if x * y == 0.0:  # x or y = 0.0
        return diff < (tolerance * tolerance)

    return diff <= tolerance * abs(x) or diff <= tolerance * abs(y)
