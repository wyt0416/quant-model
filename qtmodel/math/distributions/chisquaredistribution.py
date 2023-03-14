import math
import sys

from qtmodel.error import QTError
from qtmodel.math.distributions.gammadistribution import CumulativeGammaDistribution, GammaFunction
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution
from qtmodel.math.solvers1d.brent import Brent


class CumulativeChiSquareDistribution:
    def __init__(self, df):
        self._df = df

    def __call__(self, x):
        return CumulativeGammaDistribution(0.5 * self._df)(0.5 * x)


class NonCentralCumulativeChiSquareDistribution:
    def __init__(self, df, ncp):
        self._df = df
        self._ncp = ncp

    def __call__(self, x):
        if x <= 0.0:
            return 0.0

        errmax = 1e-12
        itrmax = 10000
        lam = 0.5 * self._ncp

        u = math.exp(-lam)
        v = u
        x2 = 0.5 * x
        f2 = 0.5 * self._df
        f_x_2n = self._df - x

        t = 0.0
        if (f2 * sys.float_info.epsilon > 0.125 and
                abs(x2 - f2) < math.sqrt(sys.float_info.epsilon) * f2):
            t = math.exp((1 - t) *
                         (2 - t / (f2 + 1))) / math.sqrt(2.0 * math.pi * (f2 + 1.0))
        else:
            t = math.exp(f2 * math.log(x2) - x2 -
                         GammaFunction().log_value(f2 + 1))

        ans = v * t

        flag = False
        n = 1
        f_2n = self._df + 2.0
        f_x_2n += 2.0

        while 1:
            if f_x_2n > 0:
                flag = True
                bound = t * x / f_x_2n
                if bound <= errmax or n > itrmax:
                    if bound > errmax:
                        QTError("didn't converge")
                    return ans
                else:
                    while 1:
                        u *= lam / n
                        v += u
                        t *= x / f_2n
                        ans += v * t
                        n += 1
                        f_2n += 2.0
                        f_x_2n += 2.0
                        if not flag and n <= itrmax:
                            break
                        bound = t * x / f_x_2n
                        if bound <= errmax or n > itrmax:
                            if bound > errmax:
                                QTError("didn't converge")
                            return ans
            else:
                while 1:
                    u *= lam / n
                    v += u
                    t *= x / f_2n
                    ans += v * t
                    n += 1
                    f_2n += 2.0
                    f_x_2n += 2.0
                    if not flag and n <= itrmax:
                        break
                    bound = t * x / f_x_2n
                    if bound <= errmax or n > itrmax:
                        if bound > errmax:
                            QTError("didn't converge")
                        return ans


class NonCentralCumulativeChiSquareSankaranApprox:
    def __init__(self, df, ncp):
        self._df = df
        self._ncp = ncp

    def __call__(self, x):
        h = 1 - 2 * (self._df + self._ncp) * (self._df + 3 * self._ncp) / (3 * pow(self._df + 2 * self._ncp, 2))
        p = (self._df + 2 * self._ncp) / pow(self._df + self._ncp, 2)
        m = (h - 1) * (1 - 3 * h)

        u = (math.pow(x / (self._df + self._ncp), h) - (1 + h * p * (h - 1 - 0.5 * (2 - h) * m * p))) / (
                h * math.sqrt(2 * p) * (1 + 0.5 * m * p))

        return CumulativeNormalDistribution()(u)


class InverseNonCentralCumulativeChiSquareDistribution:
    def __init__(self, df, ncp, max_evaluations=10, accuracy=1e-8):
        self._non_central_dist = NonCentralCumulativeChiSquareDistribution(df, ncp)
        self._guess = df + ncp
        self._max_evaluations = max_evaluations
        self._accuracy = accuracy

    def __call__(self, x):
        # first find the right side of the interval
        upper = self._guess
        evaluations = self._max_evaluations
        while self._non_central_dist(upper) < x and evaluations > 0:
            upper *= 2.0
            evaluations -= 1

        # use a Brent solver for the rest
        solver = Brent()
        solver.set_max_evaluations(evaluations)
        return solver.solve(lambda y: self._non_central_dist(y) - x,
                            self._accuracy,
                            0.75 * upper,
                            0.0 if evaluations == self._max_evaluations else 0.5 * upper,
                            upper)
