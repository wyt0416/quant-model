import math

from qtmodel.error import qt_require


class FrankCopula:
    """ Frank copula """

    def __init__(self, theta):
        qt_require(theta != 0, f"theta ({theta}) must be different from 0")
        self._theta = theta

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return -1.0 / self._theta * math.log(
            1 + (math.exp(-self._theta * x) - 1) * (math.exp(-self._theta * y) - 1) / (math.exp(-self._theta) - 1))
