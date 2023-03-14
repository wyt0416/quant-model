import math
import sys

from qtmodel.error import qt_require
from qtmodel.math.beta import incomplete_beta_function
from qtmodel.math.factorial import Factorial


class BinomialDistribution:
    """
    Binomial probability distribution function
    formula here ...
    Given an integer k it returns its probability in a Binomial
    distribution with parameters p and n.
    """

    def __init__(self, p, n: int):
        self._n = n
        if p == 0.0:
            self._log_p = -sys.float_info.max
            self._log_one_minus_p = 0.0
        elif p == 1.0:
            self._log_p = 0.0
            self._log_one_minus_p = -sys.float_info.max
        else:
            qt_require(p > 0, "negative p not allowed")
            qt_require(p < 1.0, "p>1.0 not allowed")

            self._log_p = math.log(p)
            self._log_one_minus_p = math.log(1.0 - p)

    def __call__(self, k: int):
        if k > self._n:
            return 0.0

        # p==1.0
        if self._log_p == 0.0:
            return 1.0 if k == self._n else 0.0
        # p==0.0
        elif self._log_one_minus_p == 0.0:
            return 1.0 if k == 0 else 0.0
        else:
            return math.exp(
                self.binomial_coefficient_ln(self._n, k) + k * self._log_p + (self._n - k) * self._log_one_minus_p)

    @staticmethod
    def binomial_coefficient_ln(n: int, k: int):
        qt_require(n >= k, "n<k not allowed")

        return Factorial.ln(n) - Factorial.ln(k) - Factorial.ln(n - k)

    @staticmethod
    def binomial_coefficient(n: int, k: int):
        return math.floor(0.5 + math.exp(BinomialDistribution.binomial_coefficient_ln(n, k)))


class CumulativeBinomialDistribution:
    """
    Cumulative binomial distribution function
    Given an integer k it provides the cumulative probability
    of observing kk<=k:
    formula here ...
    """

    def __init__(self, p, n: int):
        qt_require(p >= 0, "negative p not allowed")
        qt_require(p <= 1.0, "p>1.0 not allowed")
        self._n = n
        self._p = p

    def __call__(self, k: int):
        if k >= self._n:
            return 1.0
        else:
            return 1.0 - incomplete_beta_function(k + 1, self._n - k, self._p)


def peizer_pratt_method2_inversion(z, n: int):
    """
    Given an odd integer n and a real number z it returns p such that:
    1 - CumulativeBinomialDistribution((n-1)/2, n, p) = CumulativeNormalDistribution(z)
    n must be odd
    :param z:
    :param n:
    :return:
    """
    qt_require(n % 2 == 1, f"n must be an odd number: {n} not allowed")

    result = z / (n + 1.0 / 3.0 + 0.1 / (n + 1.0))
    result *= result
    result = math.exp(-result * (n + 1.0 / 6.0))
    result = 0.5 + (1 if z > 0 else -1) * math.sqrt((0.25 * (1.0 - result)))
    return result
