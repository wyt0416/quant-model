from qtmodel.error import qt_require


class ClaytonCopula:
    """ Clayton copula """

    def __init__(self, theta):
        qt_require(theta >= -1.0, f"theta ({theta}) must be greater or equal to -1")
        qt_require(theta != 0, f"theta ({theta}) must be different from 0")
        self._theta = theta

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return max(pow(pow(x, -self._theta) + pow(y, -self._theta) - 1.0, -1.0 / self._theta), 0.0)
