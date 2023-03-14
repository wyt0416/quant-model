# Copyright (C) 2003, 2004 Ferdinando Ametrano
# Copyright (C) 2003 StatPro Italia srl
# Copyright (C) 2005 Gary Kennedy
# Copyright (C) 2013 Fabien Le Floc'h
# Copyright (C) 2016 Klaus Spanderen

import math
from decimal import *
from typing import Callable

import numpy as np
import scipy.stats as st

from qtmodel.error import TestError, QTError
from qtmodel.math.comparison import close
from qtmodel.math.distributions.normaldistribution import *
from qtmodel.math.distributions.bivariatenormaldistribution import *
from qtmodel.math.distributions.bivariatestudenttdistribution import *
from qtmodel.math.distributions.chisquaredistribution import *
from qtmodel.math.distributions.gammadistribution import *
from qtmodel.math.distributions.binomialdistribution import *
from qtmodel.math.distributions.poissondistribution import PoissonDistribution, CumulativePoissonDistribution, \
    InverseCumulativePoisson
from qtmodel.math.integrals.gaussianorthogonalpolynomial import GaussLaguerrePolynomial
from qtmodel.math.integrals.gaussianquadratures import GaussLegendreIntegration, GaussChebyshevIntegration, \
    GaussChebyshev2ndIntegration, GaussLaguerreIntegration, GaussHermiteIntegration, GaussHyperbolicIntegration, \
    GaussianQuadrature, GaussGegenbauerIntegration
from qtmodel.math.integrals.gausslaguerrecosinepolynomial import GaussLaguerreCosinePolynomial, \
    GaussLaguerreSinePolynomial
from qtmodel.math.integrals.momentbasedgaussianpolynomial import MomentBasedGaussianPolynomial
from utilities import norm_test


# test functions

def inv_exp(x):
    return math.exp(-x)


def x_inv_exp(x):
    return x * math.exp(-x)


def x_normaldistribution(x):
    return x * NormalDistribution()(x)


def x_x_normaldistribution(x):
    return x * x * NormalDistribution()(x)


def inv_cosh(x):
    return 1 / math.cosh(x)


def x_inv_cosh(x):
    return x / math.cosh(x)


def x_x_nonCentralChiSquared(x):
    return x * x * st.norm.pdf(np.random.noncentral_chisquare(4.0, 1.0), x)


def x_sin_exp_nonCentralChiSquared(x):
    return x * math.sin(0.1 * x) * math.exp(0.3 * x) * st.norm.pdf(
        np.random.noncentral_chisquare(1.0, 1.0), x)


def single(i: Callable[[float], object],
           tag: str,
           f: Callable[[float], float],
           expected: float):
    calculated = i(f)
    if abs(calculated - expected) > 1.0e-4:
        raise QTError(
            f"integrating {tag} \n calculated: {calculated} \n expected: {expected}")


def single_jacobi(i: Callable[[float], object]):
    single(i, "f(x) = 1", lambda x: 1, 2)
    single(i, "f(x) = x", lambda x: x, 0)
    single(i, "f(x) = ^2", lambda x: x ** 2, 2 / 3)
    single(i, "f(x) = sin(x)", lambda x: math.sin(x), 0)
    single(i, "f(x) = cos(x)", lambda x: math.cos(x), math.sin(1.0) - math.sin(-1.0))
    single(i, "f(x) = Gaussian(x)", lambda x: NormalDistribution()(x),
           CumulativeNormalDistribution()(1.0) - CumulativeNormalDistribution()(-1.0))


def single_laguerre(i: Callable[[float], object]):
    single(i, "f(x) = exp(-x)", inv_exp, 1)
    single(i, "f(x) = x*exp(-x)", x_inv_exp, 1)
    single(i, "f(x) = Gaussian(x)", NormalDistribution(), 0.5)


def single_tabulated(f: Callable[[float], float],
                     tag: str, expected: float,
                     tolerance: float):
    order = [6, 7, 12, 20]
    quad = TabulatedGaussLegendre()
    for i in order:
        quad.order(i)
        realised = quad(f)
        if abs(realised - expected) > tolerance:
            QTError(
                f" integrating {tag}\n order {i}\n realised: {realised} \n expected: {expected}")


def test_jacobi():
    print("Testing Gauss-Jacobi integration...")
    single_jacobi(GaussLegendreIntegration(16))
    single_jacobi(GaussChebyshevIntegration(130))
    single_jacobi(GaussChebyshev2ndIntegration(130))
    single_jacobi(GaussGegenbauerIntegration(50, 0.55))


def test_laguerre():
    print("Testing Gauss-Laguerre integration...")

    single_laguerre(GaussLaguerreIntegration(16))
    single_laguerre(GaussLaguerreIntegration(150, 0.01))

    single(GaussLaguerreIntegration(16, 1.0), "f(x) = x*exp(-x)", x_inv_exp, 1.0)
    single(GaussLaguerreIntegration(32, 0.9), "f(x) = x*exp(-x)", x_inv_exp, 1.0)


def test_hermite():
    print("Testing Gauss-Hermite integration...")

    single(GaussHermiteIntegration(16), "f(x) = Gaussian(x)", NormalDistribution(), 1.0)
    single(GaussHermiteIntegration(16, 0.5), "f(x) = x*Gaussian(x)", x_normaldistribution, 0.0)
    single(GaussHermiteIntegration(64, 0.9), "f(x) = x*x*Gaussian(x)", x_x_normaldistribution, 1.0)


def test_hyperbolic():
    print("Testing Gauss hyperbolic integration...")

    single(GaussHyperbolicIntegration(16), "f(x) = 1/cosh(x)", inv_cosh, math.pi)
    single(GaussHyperbolicIntegration(16), "f(x) = x/cosh(x)", x_inv_cosh, 0.0)


def test_tabulated():
    print("Testing tabulated Gauss-Laguerre integration...")

    single_tabulated(lambda x: 1.0, "f(x) = 1", 2.0, 1.0e-13)
    single_tabulated(lambda x: x, "f(x) = x", 0.0, 1.0e-13)
    single_tabulated(lambda x: x * x, "f(x) = x^2", (2.0 / 3.0), 1.0e-13)
    single_tabulated(lambda x: x * x * x, "f(x) = x^3", 0.0, 1.0e-13)
    single_tabulated(lambda x: x * x * x * x, "f(x) = x^4", (2.0 / 5.0), 1.0e-13)


class MomentBasedGaussLaguerrePolynomial(MomentBasedGaussianPolynomial):
    def moment(self,
               i: int):
        if i == 0:
            return 1.0
        else:
            return i * self.moment(i - 1)

    def w(self, x):
        return math.exp(-x)


def test_moment_based_gaussian_polynomial():
    print("Testing moment-based Gaussian polynomials...")

    g = GaussLaguerrePolynomial()
    ml = []
    ml.append(MomentBasedGaussLaguerrePolynomial())

    # ml.append(ext.make_shared < MomentBasedGaussLaguerrePolynomial > ())

    tol = 1e-12
    for k in ml:
        for i in range(10):
            diff_alpha = abs(k.alpha(i) - g.alpha(i))
            diff_beta = abs(k.beta(i) - g.beta(i))
            if diff_alpha > tol:
                print(
                    f"failed to reproduce alpha for Laguerre quadrature\n calculated:{k.alpha(i)}\n expected:"
                    f"{g.alpha(i)}\n diff:{diff_alpha}")
            if i > 0 and diff_beta > tol:
                print(
                    f"failed to reproduce beta for Laguerre quadrature\n calculated:{k.beta(i)}\n expected:{g.beta(i)}"
                    f"\n diff:{diff_beta}")


def test_gauss_laguerre_cosine_polynomial():
    print("Testing Gauss-Laguerre-Cosine quadrature...")

    quad_cosine = GaussianQuadrature(16, GaussLaguerreCosinePolynomial(0.2))

    single(quad_cosine, "f(x) = exp(-x)", inv_exp, 1.0)
    single(quad_cosine, "f(x) = x*exp(-x)", x_inv_exp, 1.0)

    quad_sine = GaussianQuadrature(16, GaussLaguerreSinePolynomial(0.2))

    single(quad_sine, "f(x) = exp(-x)", inv_exp, 1.0)
    single(quad_sine, "f(x) = x*exp(-x)", x_inv_exp, 1.0)
