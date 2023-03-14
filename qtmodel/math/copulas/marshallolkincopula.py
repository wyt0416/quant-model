import math

from qtmodel.error import qt_require


class MarshallOlkinCopula:
    """
    Marshall-Olkin copula
    """

    def __init__(self, a1, a2):
        qt_require(a1 >= 0.0, f"1st parameter ({a1}) must be non-negative")
        qt_require(a2 >= 0.0, f"2nd parameter ({a2}) must be non-negative")
        self._a1 = 1.0 - a1
        self._a2 = 1.0 - a2

    def __call__(self, x, y):
        qt_require(0.0 <= x <= 1.0, "1st argument (" << x << ") must be in [0,1]")
        qt_require(0.0 <= y <= 1.0, "2nd argument (" << y << ") must be in [0,1]")
        return min(y * math.pow(x, self._a1), x * math.pow(y, self._a2))
