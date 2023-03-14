"""
Integral of a one-dimensional function
References:
This algorithm is a C++ implementation of the algorithm outlined in

W. Gander and W. Gautschi, Adaptive Quadrature - Revisited.
BIT, 40(1):84-101, March 2000. CS technical report:
ftp.inf.ethz.ch/pub/publications/tech-reports/3xx/306.ps.gz

The original MATLAB version can be downloaded here
http://www.inf.ethz.ch/personal/gander/adaptlob.m
"""
import math
import sys
from typing import Callable

from qtmodel.error import qt_require, QTError
from qtmodel.math.integrals.integral import Integrator
from qtmodel.types import Real


class GaussLobattoIntegral(Integrator):
    alpha_ = math.sqrt(2.0 / 3.0)
    beta_ = 1.0 / math.sqrt(5.0)
    x1_ = 0.94288241569547971906
    x2_ = 0.64185334234578130578
    x3_ = 0.23638319966214988028

    def __init__(self,
                 max_iterations: int,
                 abs_accuracy: Real,
                 rel_accuracy: Real = sys.float_info.max,
                 use_convergence_estimate: bool = True):
        super().__init__(abs_accuracy, max_iterations)
        self._rel_accuracy = rel_accuracy
        self._use_convergence_estimate = use_convergence_estimate

    def integrate(self, f: Callable[[float], float], a: Real, b: Real):
        self.set_number_of_evaluations(0)
        calc_abs_tolerance = self.calculate_abs_tolerance(f, a, b)

        self.increase_number_of_evaluations(2)
        return self.adaptiv_gauss_lobatto_step(f, a, b, f(a), f(b), calc_abs_tolerance)

    def adaptiv_gauss_lobatto_step(self,
                                   f: Callable[[float], float],
                                   a: Real,
                                   b: Real,
                                   fa: Real,
                                   fb: Real,
                                   acc: Real):
        qt_require(self.number_of_evaluations() < self.max_evaluations(),
                   "max number of iterations reached")

        h = (b - a) / 2
        m = (a + b) / 2

        mll = m - self.alpha_ * h
        ml = m - self.beta_ * h
        mr = m + self.beta_ * h
        mrr = m + self.alpha_ * h

        fmll = f(mll)
        fml = f(ml)
        fm = f(m)
        fmr = f(mr)
        fmrr = f(mrr)
        self.increase_number_of_evaluations(5)

        integral2 = (h / 6) * (fa + fb + 5 * (fml + fmr))
        integral1 = (h / 1470) * (77 * (fa + fb) + 432 * (fmll + fmrr) + 625 * (fml + fmr) + 672 * fm)

        # avoid 80 bit logic on x86 cpu
        dist = acc + (integral1 - integral2)
        if dist == acc or mll <= a or b <= mrr:
            qt_require(a < m < b, "Interval contains no more machine number")
            return integral1

        else:
            return self.adaptiv_gauss_lobatto_step(f, a, mll, fa, fmll, acc) + \
                   self.adaptiv_gauss_lobatto_step(f, mll, ml, fmll, fml, acc) + \
                   self.adaptiv_gauss_lobatto_step(f, ml, m, fml, fm, acc) + \
                   self.adaptiv_gauss_lobatto_step(f, m, mr, fm, fmr, acc) + \
                   self.adaptiv_gauss_lobatto_step(f, mr, mrr, fmr, fmrr, acc) + \
                   self.adaptiv_gauss_lobatto_step(f, mrr, b, fmrr, fb, acc)

    def calculate_abs_tolerance(self,
                                f: Callable[[float], float],
                                a: Real,
                                b: Real):
        rel_tol = max(self._rel_accuracy, sys.float_info.epsilon)

        m = (a + b) / 2
        h = (b - a) / 2
        y1 = f(a)
        y3 = f(m - self.alpha_ * h)
        y5 = f(m - self.beta_ * h)
        y7 = f(m)
        y9 = f(m + self.beta_ * h)
        y11 = f(m + self.alpha_ * h)
        y13 = f(b)

        f1 = f(m - self.x1_ * h)
        f2 = f(m + self.x1_ * h)
        f3 = f(m - self.x2_ * h)
        f4 = f(m + self.x2_ * h)
        f5 = f(m - self.x3_ * h)
        f6 = f(m + self.x3_ * h)

        acc = h * (0.0158271919734801831 * (y1 + y13)
                   + 0.0942738402188500455 * (f1 + f2)
                   + 0.1550719873365853963 * (y3 + y11)
                   + 0.1888215739601824544 * (f3 + f4)
                   + 0.1997734052268585268 * (y5 + y9)
                   + 0.2249264653333395270 * (f5 + f6)
                   + 0.2426110719014077338 * y7)

        self.increase_number_of_evaluations(13)
        if acc == 0.0 and (f1 != 0.0 or f2 != 0.0 or f3 != 0.0 or f4 != 0.0 or f5 != 0.0 or f6 != 0.0):
            QTError("can not calculate absolute accuracy from relative accuracy")

        r = 1.0
        if self._use_convergence_estimate:
            integral2 = (h / 6) * (y1 + y13 + 5 * (y5 + y9))
            integral1 = (h / 1470) * (77 * (y1 + y13) + 432 * (y3 + y11) + 625 * (y5 + y9) + 672 * y7)

            if abs(integral2 - acc) != 0.0:
                r = abs(integral1 - acc) / abs(integral2 - acc)
            if r == 0.0 or r > 1.0:
                r = 1.0

        if self._rel_accuracy != sys.float_info.max:
            return min(self.absolute_accuracy(), acc * rel_tol) / (r * sys.float_info.epsilon)
        else:
            return self.absolute_accuracy() / (r * sys.float_info.epsilon)
