import math
from abc import ABCMeta, abstractmethod
from typing import Union

from qtmodel.math.integrals.momentbasedgaussianpolynomial import MomentBasedGaussianPolynomial
from qtmodel.types import Real


class GaussLaguerreTrigonometricBase(MomentBasedGaussianPolynomial, metaclass=ABCMeta):
    def __init__(self, u: Real):
        super().__init__()
        self._u = u
        self._m = []
        self._f = []

    @abstractmethod
    def m0(self):
        pass

    @abstractmethod
    def m1(self):
        pass

    def moment_(self, n: int):  # NOLINT(bugprone-virtual-near-miss)
        _m_len = len(self._m)
        if _m_len <= n:
            self._m.extend([float('nan')] * (n + 1 - _m_len))

        if math.isnan(self._m[n]):
            if n == 0:
                self._m[0] = self.m0()
            elif n == 1:
                self._m[1] = self.m1()
            else:
                self._m[n] = (2 * n * self.moment_(n - 1) - n * (n - 1) * self.moment_(n - 2)) / (1 + self._u * self._u)

        return self._m[n]

    def fact(self, n: int):
        _f_len = len(self._f)
        if _f_len <= n:
            self._f.extend([float('nan')] * (n + 1 - _f_len))

        if math.isnan(self._f[n]):
            if n == 0:
                self._f[0] = 1.0
            else:
                self._f[n] = n * self.fact(n - 1)

        return self._f[n]


class GaussLaguerreCosinePolynomial(GaussLaguerreTrigonometricBase):
    """
    Gauss-Laguerre Cosine integration
    This class performs a 1-dimensional Gauss-Laguerre-Cosine integration.
    """

    def __init__(self, u: Union[float, int]):
        super().__init__(u)
        self._m0 = 1.0 + 1.0 / (1.0 + u * u)

    def moment(self, n: int):
        return (self.moment_(n) + self.fact(n)) / self._m0

    def w(self, x: Union[float, int]):
        return math.exp(-x) * (1 + math.cos(self._u * x)) / self._m0

    def m0(self):
        return 1 / (1 + self._u * self._u)

    def m1(self):
        return (1 - self._u * self._u) / (1 + self._u * self._u) ** 2


class GaussLaguerreSinePolynomial(GaussLaguerreTrigonometricBase):
    """
    Gauss-Laguerre Sine integration
    This class performs a 1-dimensional Gauss-Laguerre-Cosine integration.
    """

    def __init__(self, u: Union[float, int]):
        super().__init__(u)
        self._m0 = 1.0 + u / (1.0 + u * u)

    def moment(self, n: int):
        return (self.moment_(n) + self.fact(n)) / self._m0

    def w(self, x: Union[float, int]):
        return math.exp(-x) * (1 + math.sin(self._u * x)) / self._m0

    def m0(self):
        return self._u / (1 + self._u * self._u)

    def m1(self):
        return 2 * self._u / (1 + self._u * self._u) ** 2
