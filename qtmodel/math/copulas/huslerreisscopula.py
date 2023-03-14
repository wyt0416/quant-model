import math

from qtmodel.error import qt_require
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution


class HuslerReissCopula:
    """ Husler-Reiss copula """

    def __init__(self, theta):
        qt_require(
            theta >= 0,
            f"theta ({theta}) must be greater or equal to 0")
        self._theta = theta
        self._cum_normal = CumulativeNormalDistribution()

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return pow(x, self._cum_normal(
            1.0 / self._theta + 0.5 * self._theta * math.log(-math.log(x) / -math.log(y)))) * pow(y, self._cum_normal(
                1.0 / self._theta + 0.5 * self._theta * math.log(-math.log(y) / -math.log(x))))
