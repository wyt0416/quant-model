from qtmodel.error import qt_require


class FarlieGumbelMorgensternCopula:
    """ Farlie-Gumbel-Morgenstern copula """

    def __init__(self, theta):
        qt_require(-1.0 <= theta <= 1.0, f"theta ({theta}) must be in [-1,1]")
        self._theta = theta

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return x * y + self._theta * x * y * (1.0 - x) * (1.0 - y)
