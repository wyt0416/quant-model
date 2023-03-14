import math
import sys

from qtmodel.error import QTError, qt_require
from qtmodel.math.distributions.gammadistribution import GammaFunction


def beta_function(z, w):
    return math.exp(GammaFunction().log_value(z) +
                    GammaFunction().log_value(w) -
                    GammaFunction().log_value(z + w))


def beta_continued_fraction(a, b, x, accuracy=1e-16, max_iteration: int = 100):
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < sys.float_info.epsilon:
        d = sys.float_info.epsilon
    d = 1.0 / d
    result = d

    m = 1
    while m <= max_iteration:
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < sys.float_info.epsilon:
            d = sys.float_info.epsilon
        c = 1.0 + aa / c
        if abs(c) < sys.float_info.epsilon:
            c = sys.float_info.epsilon
        d = 1.0 / d
        result *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < sys.float_info.epsilon:
            d = sys.float_info.epsilon
        c = 1.0 + aa / c
        if abs(c) < sys.float_info.epsilon:
            c = sys.float_info.epsilon
        d = 1.0 / d
        del_ = d * c
        result *= del_
        if abs(del_ - 1.0) < accuracy:
            return result
        m += 1

    QTError("a or b too big, or max_iteration too small in betacf")


def incomplete_beta_function(a, b, x, accuracy=1e-16, max_iteration: int = 100):
    """
    Incomplete Beta function
    The implementation of the algorithm was inspired by
    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery, chapter 6
    """
    qt_require(a > 0.0, "a must be greater than zero")
    qt_require(b > 0.0, "b must be greater than zero")

    if x == 0.0:
        return 0.0
    elif x == 1.0:
        return 1.0
    else:
        qt_require(0.0 < x < 1.0, "x must be in [0,1]")

    result = math.exp(
        GammaFunction().log_value(a + b) - GammaFunction().log_value(a) - GammaFunction().log_value(b) + a * math.log(
            x) + b * math.log(1.0 - x))

    if x < (a + 1.0) / (a + b + 2.0):
        return result * beta_continued_fraction(a, b, x, accuracy, max_iteration) / a
    else:
        return 1.0 - result * beta_continued_fraction(b, a, 1.0 - x, accuracy, max_iteration) / b
