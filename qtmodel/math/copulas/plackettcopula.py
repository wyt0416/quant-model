import math

from qtmodel.error import qt_require


class PlackettCopula:
    """
    Plackett copula
    """

    def __init__(self, theta):
        qt_require(theta >= 0.0, "theta ({theta}) must be greater or equal to 0")
        qt_require(theta != 1.0, "theta ({theta}) must be different from 1")
        self._theta = theta

    def __call__(self, x, y):
        qt_require(0.0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0.0 <= y <= 1.0, f"2nd argument ({y}) must be in [0,1]")
        return ((1.0 + (self._theta - 1.0) * (x + y)) - math.sqrt(
            math.pow(1.0 + (self._theta - 1.0) * (x + y), 2.0) - 4.0 * x * y * self._theta * (self._theta - 1.0))) / (
                           2.0 * (self._theta - 1.0))
