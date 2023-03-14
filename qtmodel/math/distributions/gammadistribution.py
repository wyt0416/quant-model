import math
import sys

from qtmodel.error import qt_require, QTError


class CumulativeGammaDistribution:

    def __init__(self, a):
        qt_require(a > 0.0, "invalid parameter for gamma distribution")
        self._a = a

    def __call__(self, x):
        if x <= 0.0:
            return 0.0

        gln = GammaFunction().log_value(self._a)

        if x < (self._a + 1.0):
            ap = self._a
            val = 1.0 / self._a
            sum_ = val
            n = 1
            while n <= 100:
                ap += 1.0
                val *= x / ap
                sum_ += val
                if abs(val) < abs(sum_) * 3.0e-7:
                    return sum_ * math.exp(-x + self._a * math.log(x) - gln)
                n += 1
        else:
            b = x + 1.0 - self._a
            c = sys.float_info.max
            d = 1.0 / b
            h = d
            n = 1
            while n <= 100:
                an = -1.0 * n * (n - self._a)
                b += 2.0
                d = an * d + b
                if abs(d) < sys.float_info.epsilon:
                    d = sys.float_info.epsilon
                c = b + an / c
                if abs(c) < sys.float_info.epsilon:
                    c = sys.float_info.epsilon
                d = 1.0 / d
                val = d * c
                h *= val
                if abs(val - 1.0) < sys.float_info.epsilon:
                    return 1.0 - h * math.exp(-x + self._a * math.log(x) - gln)
                n += 1
        QTError("too few iterations")


class GammaFunction:
    """
    Gamma function class
    The implementation of the algorithm was inspired by
    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery, chapter 6
    """
    _c1 = 76.18009172947146
    _c2 = -86.50532032941677
    _c3 = 24.01409824083091
    _c4 = -1.231739572450155
    _c5 = 0.1208650973866179e-2
    _c6 = -0.5395239384953e-5

    @staticmethod
    def value(x):
        if x >= 1.0:
            return math.exp(GammaFunction.log_value(x))
        else:
            if x > -20.0:
                # \Gamma(x) = \frac{\Gamma(x+1)}{x}
                return GammaFunction.value(x + 1.0) / x
            else:
                # \Gamma(-x) = -\frac{\pi}{\Gamma(x)\sin(\pi x) x}
                return -math.pi / (GammaFunction.value(-x) * x * math.sin(math.pi * x))

    @staticmethod
    def log_value(x):
        qt_require(x > 0.0, "positive argument required")
        temp = x + 5.5
        temp -= (x + 0.5) * math.log(temp)
        ser = 1.000000000190015
        ser += GammaFunction._c1 / (x + 1.0)
        ser += GammaFunction._c2 / (x + 2.0)
        ser += GammaFunction._c3 / (x + 3.0)
        ser += GammaFunction._c4 / (x + 4.0)
        ser += GammaFunction._c5 / (x + 5.0)
        ser += GammaFunction._c6 / (x + 6.0)

        return -temp + math.log(2.5066282746310005 * ser / x)
