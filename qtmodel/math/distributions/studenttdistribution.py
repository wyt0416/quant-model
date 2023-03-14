import math

from qtmodel.error import qt_require
from qtmodel.math.beta import incomplete_beta_function
from qtmodel.math.distributions.gammadistribution import GammaFunction


class StudentDistribution:
    """ Student t-distribution """

    def __init__(self, n: int):
        qt_require(n > 0, "invalid parameter for t-distribution")
        self._n = n

    def __call__(self, x):
        g1 = math.exp(GammaFunction.log_value(0.5 * (self._n + 1)))
        g2 = math.exp(GammaFunction.log_value(0.5 * self._n))

        power = math.pow(1. + x * x / self._n, 0.5 * (self._n + 1))

        return g1 / (g2 * power * math.sqrt(math.pi * self._n))


class CumulativeStudentDistribution:
    """ Cumulative Student t-distribution """

    def __init__(self, n: int):
        qt_require(n > 0, "invalid parameter for t-distribution")
        self._n = n

    def __call__(self, x):
        xx = 1.0 * self._n / (x * x + self._n)
        sig = 1.0 if x > 0 else - 1.0

        return 0.5 + 0.5 * sig * (
                incomplete_beta_function(0.5 * self._n, 0.5, 1.0) - incomplete_beta_function(0.5 * self._n, 0.5,
                                                                                             xx))


class InverseCumulativeStudent:
    """ Inverse cumulative Student t-distribution """

    def __init__(self, n: int, accuracy=1e-6, max_iterations: int = 50):
        self._d = StudentDistribution(n)
        self._f = CumulativeStudentDistribution(n)
        self._accuracy = accuracy
        self._max_iterations = max_iterations

    def __call__(self, y):
        qt_require(0 <= y <= 1, "argument out of range [0, 1]")

        x = 0
        count = 0

        # do a few newton steps to find x
        x -= (self._f(x) - y) / self._d(x)
        count += 1
        while abs(self._f(x) - y) > self._accuracy and count < self._max_iterations:
            x -= (self._f(x) - y) / self._d(x)
            count += 1

        qt_require(count < self._max_iterations,
                   f"maximum number of iterations {self._max_iterations} reached in InverseCumulativeStudent, y={y} , x={x}")

        return x
