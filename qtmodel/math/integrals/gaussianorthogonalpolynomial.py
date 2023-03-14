import math
from abc import ABCMeta, abstractmethod

from qtmodel.error import qt_require, QTError, qt_assert
from qtmodel.math.comparison import close_enough
from qtmodel.math.distributions.gammadistribution import GammaFunction


class GaussianOrthogonalPolynomial(metaclass=ABCMeta):
    """
    orthogonal polynomial for Gaussian quadratures
    References:
    Gauss quadratures and orthogonal polynomials

    G.H. Gloub and J.H. Welsch: Calculation of Gauss quadrature rule.
    Math. Comput. 23 (1986), 221-230

    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery,

    The polynomials are defined by the three-term recurrence relation
    """

    @abstractmethod
    def mu_0(self):
        pass

    @abstractmethod
    def alpha(self, i: int):
        pass

    @abstractmethod
    def beta(self, i: int):
        pass

    @abstractmethod
    def w(self, x):
        pass

    def value(self, i: int, x):
        if i > 1:
            return (x - self.alpha(i - 1)) * self.value(i - 1, x) - \
                self.beta(i - 1) * self.value(i - 2, x)
        elif i == 1:
            return x - self.alpha(0)

        return 1

    def weighted_value(self, i: int, x):
        return math.sqrt(self.w(x)) * self.value(i, x)


class GaussLaguerrePolynomial(GaussianOrthogonalPolynomial):
    """
    Gauss-Laguerre polynomial
    """

    def __init__(self, s=0.0):
        qt_require(s > -1.0, "s must be bigger than -1")
        self._s = s

    def mu_0(self):
        return math.exp(GammaFunction().log_value(self._s + 1))

    def alpha(self, i: int):
        return 2 * i + 1 + self._s

    def beta(self, i: int):
        return i * (i + self._s)

    def w(self, x):
        return math.pow(x, self._s) * math.exp(-x)


class GaussHermitePolynomial(GaussianOrthogonalPolynomial):
    """
    Gauss-Hermite polynomial
    """

    def __init__(self, mu=0.0):
        qt_require(mu > -0.5, "mu must be bigger than -0.5")
        self._mu = mu

    def mu_0(self):
        return math.exp(GammaFunction().log_value(self._mu + 0.5))

    def alpha(self, i: int):
        return 0.0

    def beta(self, i: int):
        return i / 2.0 + self._mu if (i % 2) != 0 else i / 2.0

    def w(self, x):
        return math.pow(abs(x), 2 * self._mu) * math.exp(-x * x)


class GaussJacobiPolynomial(GaussianOrthogonalPolynomial):
    """
    Gauss-Jacobi polynomial
    """

    def __init__(self, alpha, beta):
        qt_require(alpha + beta > -2.0, "alpha+beta must be bigger than -2")
        qt_require(alpha > -1.0, "alpha must be bigger than -1")
        qt_require(beta > -1.0, "beta  must be bigger than -1")
        self._alpha = alpha
        self._beta = beta

    def mu_0(self):
        return math.pow(2.0, self._alpha + self._beta + 1) * math.exp(GammaFunction().log_value(self._alpha + 1) +
                                                                      GammaFunction().log_value(self._beta + 1) - GammaFunction().log_value(self._alpha + self._beta + 2))

    def alpha(self, i: int):
        num = self._beta * self._beta - self._alpha * self._alpha
        denom = (2.0 * i + self._alpha + self._beta) * \
            (2.0 * i + self._alpha + self._beta + 2)

        if close_enough(denom, 0.0):
            if not close_enough(num, 0.0):
                QTError("can't compute a_k for jacobi integration\n")
            else:
                # l'Hospital
                num = 2 * self._beta
                denom = 2 * (2.0 * i + self._alpha + self._beta + 1)

                qt_assert(
                    not close_enough(
                        denom,
                        0.0),
                    "can't compute a_k for jacobi integration\n")

        return num / denom

    def beta(self, i: int):
        num = 4.0 * i * (i + self._alpha) * (i + self._beta) * \
            (i + self._alpha + self._beta)
        denom = (2.0 * i + self._alpha + self._beta) * (2.0 * i + self._alpha + self._beta) * \
            ((2.0 * i + self._alpha + self._beta) * (2.0 * i + self._alpha + self._beta) - 1)

        if close_enough(denom, 0.0):
            if not close_enough(num, 0.0):
                QTError("can't compute b_k for jacobi integration\n")
            else:
                # l'Hospital
                num = 4.0 * i * (i + self._beta) * \
                    (2.0 * i + 2 * self._alpha + self._beta)
                denom = 2.0 * (2.0 * i + self._alpha + self._beta)
                denom *= denom - 1
                qt_assert(
                    not close_enough(
                        denom,
                        0.0),
                    "can't compute b_k for jacobi integration\n")
        return num / denom

    def w(self, x):
        return math.pow(1 - x, self._alpha) * math.pow(1 + x, self._beta)


class GaussLegendrePolynomial(GaussJacobiPolynomial):
    """
    Gauss-Legendre polynomial
    """

    def __init__(self):
        super().__init__(0.0, 0.0)


class GaussChebyshevPolynomial(GaussJacobiPolynomial):
    """
    Gauss-Chebyshev polynomial
    """

    def __init__(self):
        super().__init__(-0.5, -0.5)


class GaussChebyshev2ndPolynomial(GaussJacobiPolynomial):
    """
    Gauss-Chebyshev polynomial (second kind)
    """

    def __init__(self):
        super().__init__(0.5, 0.5)


class GaussGegenbauerPolynomial(GaussJacobiPolynomial):
    """
    Gauss-Gegenbauer polynomial
    """

    def __init__(self, lamb):
        super().__init__(lamb - 0.5, lamb - 0.5)


class GaussHyperbolicPolynomial(GaussianOrthogonalPolynomial):
    """
    Gauss hyperbolic polynomial
    """

    def mu_0(self):
        return math.pi

    def alpha(self, i: int):
        return 0.0

    def beta(self, i: int):
        return (math.pi / 2) * (math.pi / 2) * i * i if i != 0 else math.pi

    def w(self, x):
        return 1 / math.cosh(x)
