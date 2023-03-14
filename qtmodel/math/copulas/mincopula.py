from qtmodel.error import qt_require


class MinCopula:
    """
    min copula
    """

    def __call__(self, x, y):
        qt_require(0.0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0.0 <= y <= 1.0, f"2nd argument ({y}) must be in [0,1]")
        return max(x + y - 1.0, 0.0)
