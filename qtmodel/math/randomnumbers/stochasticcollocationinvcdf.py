import math
from typing import Callable

from qtmodel.math.distributions.normaldistribution import InverseCumulativeNormal, CumulativeNormalDistribution
from qtmodel.math.integrals.gaussianquadratures import GaussHermiteIntegration
from qtmodel.math.interpolations.lagrangeinterpolation import LagrangeInterpolation
from qtmodel.types import Real


def g(sigma: Real, x: list, inv_cdf: Callable[[Real], Real]):
    _x_len = len(x)
    y = [None] * _x_len
    normal_cdf = CumulativeNormalDistribution()

    for i in range(_x_len):
        y[i] = inv_cdf(normal_cdf(x[i] / sigma))

    return y


class StochasticCollocationInvCDF:
    """
    Stochastic collocation inverse cumulative distribution function

    References:
    L.A. Grzelak, J.A.S. Witteveen, M.Suárez-Taboada, C.W. Oosterlee,
    The Stochastic Collocation Monte Carlo Sampler: Highly efficient
    sampling from “expensive” distributions
    http://papers.ssrn.com/sol3/papers.cfm?abstract_id=2529691
    """

    def __init__(self,
                 inv_cdf: Callable[[Real], Real],
                 lagrange_order: int,
                 p_max: Real = None,
                 p_min: Real = None):
        _x_list = GaussHermiteIntegration(lagrange_order).x()
        self._x = [math.sqrt(2) * i for i in _x_list]
        self._sigma = self._x[-1] / InverseCumulativeNormal()(p_max) if p_max is not None else self._x[0] / InverseCumulativeNormal()(p_min) if p_min is not None else 1.0
        self._y = g(self._sigma, self._x, inv_cdf)
        self._interpl = LagrangeInterpolation(self._x, self._y)

    def value(self, x: Real):
        return self._interpl(x * self._sigma, True)

    def __call__(self, u: Real):
        return self.value(InverseCumulativeNormal()(u))
