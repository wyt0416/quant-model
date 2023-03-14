"""
Incomplete Gamma function

The implementation of the algorithm was inspired by
"Numerical Recipes in C", 2nd edition,
Press, Teukolsky, Vetterling, Flannery, chapter 6
"""
import math
import sys

from qtmodel.error import qt_require, QTError
from qtmodel.math.distributions.gammadistribution import GammaFunction


def incomplete_gamma_function(a, x, accuracy=1.0e-13, max_iteration: int = 100):
    qt_require(a > 0.0, "non-positive a is not allowed")
    qt_require(x >= 0.0, "negative x non allowed")

    if x < (a + 1.0):
        # Use the series representation
        return incomplete_gamma_function_series_repr(a, x, accuracy, max_iteration)
    else:
        # Use the continued fraction representation
        return 1.0 - incomplete_gamma_function_continued_fraction_repr(a, x, accuracy, max_iteration)


def incomplete_gamma_function_series_repr(a, x, accuracy=1.0e-13, max_iteration: int = 100):
    if x == 0.0:
        return 0.0

    gln = GammaFunction().log_value(a)
    ap = a
    del_ = 1.0 / a
    sum_ = del_
    for n in range(1, max_iteration + 1):
        ap += 1
        del_ *= x / ap
        sum_ += del_
        if abs(del_) < abs(sum_) * accuracy:
            return sum_ * math.exp(-x + a * math.log(x) - gln)

    QTError("accuracy not reached")


def incomplete_gamma_function_continued_fraction_repr(a, x, accuracy=1.0e-13, max_iteration: int = 100):
    gln = GammaFunction().log_value(a)
    b = x + 1.0 - a
    c = 1.0 / sys.float_info.epsilon
    d = 1.0 / b
    h = d
    for i in range(1, max_iteration + 1):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < sys.float_info.epsilon:
            d = sys.float_info.epsilon
        c = b + an / c
        if abs(c) < sys.float_info.epsilon:
            c = sys.float_info.epsilon
        d = 1.0 / d
        del_ = d * c
        h *= del_
        if abs(del_ - 1.0) < accuracy:
            return math.exp(-x + a * math.log(x) - gln) * h

    QTError("accuracy not reached")
