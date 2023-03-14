import math

from qtmodel.error import qt_require


class GalambosCopula:
    """ Galambos copula """

    def __init__(self, theta):
        qt_require(theta >= 0, f"theta ({theta}) must be greater or equal to 0")
        self._theta = theta

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return x * y * math.exp(
            pow(pow(-math.log(x), -self._theta) + pow(-math.log(y), -self._theta), -1 / self._theta))
