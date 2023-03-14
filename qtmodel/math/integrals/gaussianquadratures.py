import math
from typing import List, Any

from qtmodel.error import QTError
from qtmodel.math.integrals.gaussianorthogonalpolynomial import GaussianOrthogonalPolynomial, GaussLaguerrePolynomial, \
    GaussHermitePolynomial, GaussJacobiPolynomial, GaussHyperbolicPolynomial
from qtmodel.math.matrixutilities.tqreigendecomposition import TqrEigenDecomposition, EigenVectorCalculationTypes, \
    ShiftStrategyTypes


class GaussianQuadrature:
    """
    Integral of a 1-dimensional function using the Gauss quadratures method
    References:
    Gauss quadratures and orthogonal polynomials

    G.H. Gloub and J.H. Welsch: Calculation of Gauss quadrature rule.
    Math. Comput. 23 (1986), 221-230

    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery,
    """

    def __init__(self, n: int, orth_poly: GaussianOrthogonalPolynomial):
        self._x: List[Any] = [None] * n
        self._w: List[Any] = [None] * n
        # set-up matrix to compute the roots and the weights
        e: List[Any] = [None] * (n - 1)

        i = 1
        while i < n:
            self._x[i] = orth_poly.alpha(i)
            e[i - 1] = math.sqrt(orth_poly.beta(i))
            i += 1

        self._x[0] = orth_poly.alpha(0)

        tqr = TqrEigenDecomposition(self._x,
                                    e,
                                    EigenVectorCalculationTypes.OnlyFirstRowEigenVector,
                                    ShiftStrategyTypes.Overrelaxation)
        self._x = tqr.eigenvalues()
        ev = tqr.eigenvectors()

        mu_0 = orth_poly.mu_0()
        i = 0
        while i < n:
            self._w[i] = mu_0 * ev[0, i] * ev[0, i] / orth_poly.w(self._x[i])
            i += 1

    def __call__(self, f):
        sum_ = 0.0
        i = self.order() - 1
        while i >= 0:
            sum_ += self._w[i] * f(self._x[i])
            i -= 1
        return sum_

    def order(self):
        return len(self._x)

    def weights(self):
        return self._w

    def x(self):
        return self._x


class GaussLaguerreIntegration(GaussianQuadrature):
    """
    generalized Gauss-Laguerre integration
    This class performs a 1-dimensional Gauss-Laguerre integration.
    """

    def __init__(self, n: int, s=0.0):
        super().__init__(n, GaussLaguerrePolynomial(s))


class GaussHermiteIntegration(GaussianQuadrature):
    """
    generalized Gauss-Hermite integration
    This class performs a 1-dimensional Gauss-Hermite integration.
    """

    def __init__(self, n: int, mu=0.0):
        super().__init__(n, GaussHermitePolynomial(mu))


class GaussJacobiIntegration(GaussianQuadrature):
    """
    Gauss-Jacobi integration
    This class performs a 1-dimensional Gauss-Jacobi integration.
    """
    def __init__(self, n: int, alpha, beta):
        super().__init__(n, GaussJacobiPolynomial(alpha, beta))


class GaussHyperbolicIntegration(GaussianQuadrature):
    """
    Gauss-Hyperbolic integration
    This class performs a 1-dimensional Gauss-Hyperbolic integration.
    """
    def __init__(self, n: int):
        super().__init__(n, GaussHyperbolicPolynomial())


class GaussLegendreIntegration(GaussianQuadrature):
    """
    Gauss-Legendre integration
    /*! This class performs a 1-dimensional Gauss-Legendre integration.
    """

    def __init__(self, n: int):
        super().__init__(n, GaussJacobiPolynomial(0.0, 0.0))


class GaussChebyshevIntegration(GaussianQuadrature):
    """
    Gauss-Chebyshev integration
    This class performs a 1-dimensional Gauss-Chebyshev integration.
    """

    def __init__(self, n: int):
        super().__init__(n, GaussJacobiPolynomial(-0.5, -0.5))


class GaussChebyshev2ndIntegration(GaussianQuadrature):
    """
    Gauss-Chebyshev integration (second kind)
    This class performs a 1-dimensional Gauss-Chebyshev integration.
    """

    def __init__(self, n: int):
        super().__init__(n, GaussJacobiPolynomial(0.5, 0.5))


class GaussGegenbauerIntegration(GaussianQuadrature):
    """
    Gauss-Gegenbauer integration
    This class performs a 1-dimensional Gauss-Gegenbauer integration.
    """
    def __init__(self, n: int, lambda_):
        super().__init__(n, GaussJacobiPolynomial(lambda_-0.5, lambda_-0.5))


class TabulatedGaussLegendre:
    """
    tabulated Gauss-Legendre quadratures
    """
    # Abscissas and Weights from Abramowitz and Stegun

    # order 6
    x6 = [0.238619186083197,
          0.661209386466265,
          0.932469514203152]

    w6 = [0.467913934572691,
          0.360761573048139,
          0.171324492379170]

    n6 = 3

    # order 7
    x7 = [0.000000000000000,
          0.405845151377397,
          0.741531185599394,
          0.949107912342759]

    w7 = [0.417959183673469,
          0.381830050505119,
          0.279705391489277,
          0.129484966168870]

    n7 = 4

    # order 12
    x12 = [0.125233408511469,
           0.367831498998180,
           0.587317954286617,
           0.769902674194305,
           0.904117256370475,
           0.981560634246719]

    w12 = [0.249147045813403,
           0.233492536538355,
           0.203167426723066,
           0.160078328543346,
           0.106939325995318,
           0.047175336386512]

    n12 = 6

    # order 20
    x20 = [0.076526521133497,
           0.227785851141645,
           0.373706088715420,
           0.510867001950827,
           0.636053680726515,
           0.746331906460151,
           0.839116971822219,
           0.912234428251326,
           0.963971927277914,
           0.993128599185095]

    w20 = [0.152753387130726,
           0.149172986472604,
           0.142096109318382,
           0.131688638449177,
           0.118194531961518,
           0.101930119817240,
           0.083276741576704,
           0.062672048334109,
           0.040601429800387,
           0.017614007139152]

    n20 = 10

    def __init__(self, n: int = 20):
        self._order = None
        self._w = None
        self._x = None
        self._n = None
        self.order(n)

    def __call__(self, f):
        assert self._w is not None, "Null weights"
        assert self._x is not None, "Null abscissas"

        is_order_odd = self._order & 1

        if is_order_odd:
            assert self._n > 0, "assume at least 1 point in quadrature"
            val = self._w[0] * f(self._x[0])
            start_idx = 1
        else:
            val = 0.0
            start_idx = 0

        i = start_idx
        while i < self._n:
            val += self._w[i] * f(self._x[i])
            val += self._w[i] * f(-self._x[i])
            i += 1

        return val

    def order(self, order: int = None):
        if order is not None:
            if order == 6:
                self._order = order
                self._x = self.x6
                self._w = self.w6
                self._n = self.n6
            elif order == 7:
                self._order = order
                self._x = self.x7
                self._w = self.w7
                self._n = self.n7
            elif order == 12:
                self._order = order
                self._x = self.x12
                self._w = self.w12
                self._n = self.n12
            elif order == 20:
                self._order = order
                self._x = self.x20
                self._w = self.w20
                self._n = self.n20
            else:
                QTError(f"order {order} not supported")
        else:
            return self._order

