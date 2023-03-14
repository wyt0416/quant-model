from qtmodel.error import qt_require
from qtmodel.math.distributions.bivariatenormaldistribution import BivariateCumulativeNormalDistributionWe04DP
from qtmodel.math.distributions.normaldistribution import InverseCumulativeNormal


class GaussianCopula:
    """
    Gaussian copula
    """
    def __init__(self, rho):
        qt_require(-1.0 <= rho <= 1.0, f"rho ({rho}) must be in [-1,1]")
        self._rho = rho
        self._bivariate_normal_cdf = BivariateCumulativeNormalDistributionWe04DP(self._rho)
        self._inv_cum_normal = InverseCumulativeNormal()

    def __call__(self, x, y):
        qt_require(0 <= x <= 1.0, f"1st argument ({x}) must be in [0,1]")
        qt_require(0 <= y <= 1.0, f"2st argument ({y}) must be in [0,1]")
        return self._bivariate_normal_cdf(self._inv_cum_normal(x), self._inv_cum_normal(y))

