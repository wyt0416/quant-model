"""
References:
Gauss quadratures and orthogonal polynomials

G.H. Gloub and J.H. Welsch: Calculation of Gauss quadrature rule.
Math. Comput. 23 (1986), 221-230,
http://web.stanford.edu/class/cme335/spr11/S0025-5718-69-99647-1.pdf

M. Morandi Cecchi and M. Redivo Zaglia, Computing the coefficients
of a recurrence formula for numerical integration by moments and
modified moments.
http://ac.els-cdn.com/0377042793901522/1-s2.0-0377042793901522-main.pdf?_tid=643d5dca-a05d-11e6-9a56-00000aab0f27&acdnat=1478023545_cf7c87cba4cc9e37a136e68a2564d411
"""
import math
from abc import ABCMeta, abstractmethod

from qtmodel.error import qt_require
from qtmodel.math.comparison import close_enough
from qtmodel.math.integrals.gaussianorthogonalpolynomial import GaussianOrthogonalPolynomial


class MomentBasedGaussianPolynomial(GaussianOrthogonalPolynomial, metaclass=ABCMeta):
    def __init__(self):
        self._z = [[]]
        self._b = []
        self._c = []

    def mu_0(self):
        m0 = self.moment(0)
        qt_require(close_enough(m0, 1.0), "zero moment must by one.")

        return self.moment(0)

    def alpha(self, i: int):
        return self.alpha_(i)

    def beta(self, i: int):
        return self.beta_(i)

    @abstractmethod
    def moment(self, i: int):
        pass

    def alpha_(self, i: int):
        _b_len = len(self._b)
        if _b_len <= i:
            self._b.extend([float('nan')] * (i + 1 - _b_len))

        if math.isnan(self._b[i]):
            if i == 0:
                self._b[i] = self.moment(1)
            else:
                tmp = -self.z(i - 1, i) / self.z(i - 1, i - 1) + self.z(i, i + 1) / self.z(i, i)
                self._b[i] = tmp

        return self._b[i]

    def beta_(self, i: int):
        if i == 0:
            return 1.0

        _c_len = len(self._c)
        if _c_len <= i:
            self._c.extend([float('nan')] * (i + 1 - _c_len))

        if math.isnan(self._c[i]):
            tmp = self.z(i, i) / self.z(i - 1, i - 1)
            self._c[i] = tmp

        return self._c[i]

    def z(self, k: int, i: int):
        if k == -1:
            return 0.0

        rows = len(self._z)
        cols = len(self._z[0])

        if cols <= i:
            for l in range(rows):
                _len = len(self._z[l])
                self._z[l].extend([float('nan')] * (i + 1 - _len))

        if rows <= k:
            _z_len = len(self._z)
            self._z.extend([[float('nan')] * (len(self._z[0]))] * (k + 1 - _z_len))

        if math.isnan(self._z[k][i]):
            if k == 0:
                self._z[k][i] = self.moment(i)
            else:
                tmp = self.z(k - 1, i + 1) - self.alpha_(k - 1) * self.z(k - 1, i) - self.beta_(k - 1) * self.z(k - 2, i)
                self._z[k][i] = tmp

        return self._z[k][i]
