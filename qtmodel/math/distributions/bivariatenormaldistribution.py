import math

from qtmodel.error import qt_require, QTError
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution
from qtmodel.math.integrals.gaussianquadratures import TabulatedGaussLegendre


class BivariateCumulativeNormalDistributionDr78:
    """
    Cumulative bivariate normal distribution function
    Drezner (1978) algorithm, six decimal places accuracy.

    For this implementation see
   "Option pricing formulas", E.G. Haug, McGraw-Hill 1998
    """

    _x = [
        0.24840615,
        0.39233107,
        0.21141819,
        0.03324666,
        0.00082485334
    ]

    _y = [
        0.10024215,
        0.48281397,
        1.06094980,
        1.77972940,
        2.66976040000
    ]

    def __init__(self, rho):
        qt_require(rho >= -1.0, f"rho must be >= -1.0 ({rho} not allowed)")
        qt_require(rho <= 1.0, f"rho must be <= 1.0 ({rho} not allowed)")
        self._rho = rho
        self._rho2 = rho * rho

    def __call__(self, a, b):
        cum_normal_dist = CumulativeNormalDistribution()
        cum_norm_dist_a = cum_normal_dist(a)
        cum_norm_dist_b = cum_normal_dist(b)
        max_cum_norm_dist_ab = max(cum_norm_dist_a, cum_norm_dist_b)
        min_cum_norm_dist_ab = min(cum_norm_dist_a, cum_norm_dist_b)

        if 1.0 - max_cum_norm_dist_ab < 1e-15:
            return min_cum_norm_dist_ab

        if min_cum_norm_dist_ab < 1e-15:
            return min_cum_norm_dist_ab

        a1 = a / math.sqrt(2.0 * (1.0 - self._rho2))
        b1 = b / math.sqrt(2.0 * (1.0 - self._rho2))

        result = -1.0

        if a <= 0.0 and b <= 0 and self._rho <= 0:
            sum_ = 0.0
            i = 0
            while i < 5:
                j = 0
                while j < 5:
                    sum_ += self._x[i] * self._x[j] * math.exp(
                        a1 * (2.0 * self._y[i] - a1) + b1 * (2.0 * self._y[j] - b1) + 2.0 * self._rho * (
                                self._y[i] - a1) * (self._y[j] - b1))
                    j += 1
                i += 1
            result = math.sqrt(1.0 - self._rho2) / math.pi * sum_
        elif a <= 0 and b >= 0 and self._rho >= 0:
            biv_cum_normal_dist = BivariateCumulativeNormalDistributionDr78(-self._rho)
            result = cum_norm_dist_a - biv_cum_normal_dist(a, -b)
        elif a >= 0.0 and b <= 0.0 and self._rho >= 0.0:
            biv_cum_normal_dist = BivariateCumulativeNormalDistributionDr78(-self._rho)
            result = cum_norm_dist_b - biv_cum_normal_dist(-a, b)
        elif a >= 0.0 and b >= 0.0 and self._rho <= 0.0:
            result = cum_norm_dist_a + cum_norm_dist_b - 1.0 + self(-a, -b)
        elif a * b * self._rho > 0.0:
            rho1 = (self._rho * a - b) * (1.0 if a > 0.0 else -1.0) / math.sqrt(a * a - 2.0 * self._rho * a * b + b * b)
            biv_cum_normal_dist = BivariateCumulativeNormalDistributionDr78(rho1)

            rho2 = (self._rho * b - a) * (1.0 if b > 0.0 else -1.0) / math.sqrt(a * a - 2.0 * self._rho * a * b + b * b)
            cbnd2 = BivariateCumulativeNormalDistributionDr78(rho2)

            delta = (1.0 - (1.0 if a > 0.0 else -1.0) * (1.0 if b > 0.0 else -1.0)) / 4.0

            result = biv_cum_normal_dist(a, 0.0) + cbnd2(b, 0.0) - delta

        else:
            QTError("case not handled")

        return result


class eqn3:  # Relates to eqn3 Genz 2004
    def __init__(self, h, k, asr):
        self._hk = h * k
        self._asr = asr
        self._hs = (h * h + k * k) / 2

    def __call__(self, x):
        sn = math.sin(self._asr * (-x + 1) * 0.5)
        return math.exp((sn * self._hk - self._hs) / (1.0 - sn * sn))


class eqn6:  # Relates to eqn6 Genz 2004

    def __init__(self, a, c, d, bs, hk):
        self._a = a
        self._c = c
        self._d = d
        self._bs = bs
        self._hk = hk

    def __call__(self, x):
        xs = self._a * (-x + 1)
        xs = abs(xs * xs)
        rs = math.sqrt(1 - xs)
        asr = -(self._bs / xs + self._hk) / 2
        if asr > -100.0:
            return (self._a * math.exp(asr) *
                    (math.exp(-self._hk * (1 - rs) / (2 * (1 + rs))) / rs -
                     (1 + self._c * xs * (1 + self._d * xs))))
        else:
            return 0.0


class BivariateCumulativeNormalDistributionWe04DP:
    """
    Cumulative bivariate normal distibution function (West 2004)
    The implementation derives from the article "Better
    Approximations To Cumulative Normal Distibutions", Graeme
    West, Dec 2004 available at www.finmod.co.za. Also available
    in Wilmott Magazine, 2005, (May), 70-76, The main code is a
    port of the C++ code at www.finmod.co.za/cumfunctions.zip.

    The algorithm is based on the near double-precision algorithm
    described in "Numerical Computation of Rectangular Bivariate
    an Trivariate Normal and t Probabilities", Genz (2004),
    Statistics and Computing 14, 151-160. (available at
    www.sci.wsu.edu/math/faculty/henz/homepage)
    """

    def __init__(self, rho):
        qt_require(rho >= -1.0, f"rho must be >= -1.0 ({rho} not allowed)")
        qt_require(rho <= 1.0, f"rho must be <= 1.0 ({rho} not allowed)")
        self._correlation = rho
        self._cumnorm = CumulativeNormalDistribution()

    def __call__(self, a, b):
        """
        The implementation is described at section 2.4 "Hybrid
        Numerical Integration Algorithms" of "Numerical Computation
        of Rectangular Bivariate an Trivariate Normal and t
        Probabilities", Genz (2004), Statistics and Computing 14,
        151-160. (available at
        www.sci.wsu.edu/math/faculty/henz/homepage)

        The Gauss-Legendre quadrature have been extracted to
        TabulatedGaussLegendre (x,w zero-based)

        Tthe functions ot be integrated numerically have been moved
        to classes eqn3 and eqn6

        Change some magic numbers to PI
        :param a:
        :param b:
        :return:
        """
        gaussLegendreQuad = TabulatedGaussLegendre(20)
        if abs(self._correlation) < 0.3:
            gaussLegendreQuad.order(6)
        elif abs(self._correlation) < 0.75:
            gaussLegendreQuad.order(12)

        h = -a
        k = -b
        hk = h * k
        bvn = 0.0

        if abs(self._correlation) < 0.925:
            if abs(self._correlation) > 0:
                asr = math.asin(self._correlation)
                f = eqn3(h, k, asr)
                bvn = gaussLegendreQuad(f)
                bvn *= asr * (0.25 / math.pi)
            bvn += self._cumnorm(-h) * self._cumnorm(-k)
        else:
            if self._correlation < 0:
                k *= -1
                hk *= -1
            if abs(self._correlation) < 1:
                ass = (1 - self._correlation) * (1 + self._correlation)
                a = math.sqrt(ass)
                bs = (h - k) * (h - k)
                c = (4 - hk) / 8
                d = (12 - hk) / 16
                asr = -(bs / ass + hk) / 2
                if asr > -100:
                    bvn = a * math.exp(asr) * (1 - c * (bs - ass) * (1 - d * bs / 5) / 3 + c * d * ass * ass / 5)
                if -hk < 100:
                    b = math.sqrt(bs)
                    bvn -= math.exp(-hk / 2) * 2.506628274631 * self._cumnorm(-b / a) * b * (1 - c * bs * (1 - d * bs / 5) / 3)
                a /= 2
                f = eqn6(a, c, d, bs, hk)
                bvn += gaussLegendreQuad(f)
                bvn /= (-2.0 * math.pi)

            if self._correlation > 0:
                bvn += self._cumnorm(-max(h, k))
            else:
                bvn *= -1
                if k > h:
                    # evaluate cumnorm where it is most precise, that
                    # is in the lower tail because of double accuracy
                    # around 0.0 vs around 1.0
                    if h >= 0:
                        bvn += self._cumnorm(-h) - self._cumnorm(-k)
                    else:
                        bvn += self._cumnorm(k) - self._cumnorm(h)

        return bvn
