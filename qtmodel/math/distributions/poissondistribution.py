import math
import sys

from qtmodel.error import qt_require
from qtmodel.math.factorial import Factorial
from qtmodel.math.incompletegamma import incomplete_gamma_function


class PoissonDistribution:
    """ Poisson distribution function """
    def __init__(self, mu):
        qt_require(mu >= 0.0, f"mu must be non negative ({mu} not allowed)")
        self._mu = mu
        if mu != 0.0:
            self._log_mu = math.log(mu)

    def __call__(self, k: int):
        if self._mu == 0.0:
            if k == 0:
                return 1.0
            else:
                return 0.0

        log_factorial = Factorial.ln(k)
        return math.exp(k * math.log(self._mu) - log_factorial - self._mu)


class CumulativePoissonDistribution:
    """
    Cumulative Poisson distribution function
    This function provides an approximation of the
    integral of the Poisson distribution.

    For this implementation see
    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery, chapter 6
    """

    def __init__(self, mu):
        self._mu = mu

    def __call__(self, k: int):
        return 1.0 - incomplete_gamma_function(k + 1, self._mu)


class InverseCumulativePoisson:
    """ Inverse cumulative Poisson distribution function """

    def __init__(self, lambda_=1.0):
        qt_require(lambda_ > 0.0, "lambda must be positive")
        self.lambda_ = lambda_

    def __call__(self, x):
        qt_require(0.0 <= x <= 1.0,
                   "Inverse cumulative Poisson distribution is only defined on the interval [0,1]")

        if x == 1.0:
            return sys.float_info.max

        sum_ = 0.0
        index = 0
        while x > sum_:
            sum_ += self.calc_summand(index)
            index += 1

        return index - 1

    def calc_summand(self, index: int):
        return math.exp(-self.lambda_) * math.pow(self.lambda_, int(index)) / Factorial.get(index)
