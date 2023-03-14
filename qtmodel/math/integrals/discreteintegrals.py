"""
References:
Levy, D. Numerical Integration
http://www2.math.umd.edu/~dlevy/classes/amsc466/lecture-notes/integration-chap.pdf
"""
import sys
from typing import Callable

from qtmodel.error import qt_require
from qtmodel.math.array import generate_array
from qtmodel.math.integrals.integral import Integrator


class DiscreteTrapezoidIntegral:
    def __call__(self, x: list, f: list):
        n = len(f)
        qt_require(n == len(x), "inconsistent size")

        acc = []
        for i in range(n - 1):
            acc.append((x[i + 1] - x[i]) * (f[i] + f[i + 1]))

        return 0.5 * sum(acc)


class DiscreteSimpsonIntegral:
    def __call__(self, x: list, f: list):
        n = len(f)
        qt_require(n == len(x), "inconsistent size")

        acc = []

        for j in range(0, n - 2, 2):
            dxj = x[j + 1] - x[j]
            dxjp1 = x[j + 2] - x[j + 1]

            alpha = -dxjp1 * (2 * x[j] - 3 * x[j + 1] + x[j + 2])
            dd = x[j + 2] - x[j]
            k = dd / (6 * dxjp1 * dxj)
            beta = dd * dd
            gamma = dxj * (x[j] - 3 * x[j + 1] + 2 * x[j + 2])

            acc.append(k * alpha * f[j] + k * beta * f[j + 1] + k * gamma * f[j + 2])

        if (n & 1) == 0:
            acc.append(0.5 * (x[n - 1] - x[n - 2]) * (f[n - 1] + f[n - 2]))

        return sum(acc)


class DiscreteTrapezoidIntegrator(Integrator):
    def __init__(self, evaluations: int):
        super().__init__(sys.float_info.max, evaluations)

    def integrate(self, f: Callable[[float], float], a, b):
        x = generate_array(self.max_evaluations(), a, (b-a)/(self.max_evaluations()-1))
        fv = list(map(f, x))

        self.increase_number_of_evaluations(self.max_evaluations())
        return DiscreteTrapezoidIntegral()(x, fv)


class DiscreteSimpsonIntegrator(Integrator):
    def __init__(self, evaluations: int):
        super().__init__(sys.float_info.max, evaluations)

    def integrate(self, f: Callable[[float], float], a, b):
        x = generate_array(self.max_evaluations(), a, (b - a) / (self.max_evaluations() - 1))
        fv = list(map(f, x))

        self.increase_number_of_evaluations(self.max_evaluations())
        return DiscreteSimpsonIntegral()(x, fv)
