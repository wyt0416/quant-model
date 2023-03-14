import math
import sys
from typing import List, Optional

from qtmodel.error import qt_require
from qtmodel.types import Real


class AbcdMathFunction:
    """ Abcd functional form """

    def __init__(self,
                 a: Real = 0.002,
                 b: Real = 0.001,
                 c: Real = 0.16,
                 d: Real = 0.0005,
                 abcd: list = None):
        if abcd is None:
            self._a = a
            self._b = b
            self._c = c
            self._d = d
            self._abcd = [None] * 4
            self._dabcd = [None] * 4
            self._abcd[0] = self._a
            self._abcd[1] = self._b
            self._abcd[2] = self._c
            self._abcd[3] = self._d
            self._da = None
            self._db = None
            self._pa = None
            self._pb = None
            self._K = None
            self._dibc = None
            self._diacplusbcc = None
            self._initialize()

        else:
            self._abcd = abcd
            self._dabcd: List[Optional[Real]] = [None] * 4
            self._a = self._abcd[0]
            self._b = self._abcd[1]
            self._c = self._abcd[2]
            self._d = self._abcd[3]
            self._initialize()

    def _initialize(self):
        self.validate(self._a, self._b, self._c, self._d)
        self._da = self._b - self._c * self._a
        self._db = -self._c * self._b
        self._dabcd[0] = self._da
        self._dabcd[1] = self._db
        self._dabcd[2] = self._c
        self._dabcd[3] = 0.0

        self._pa = -(self._a + self._b / self._c) / self._c
        self._pb = -self._b / self._c
        self._K = 0.0

        self._dibc = self._b / self._c
        self._diacplusbcc = self._a / self._c + self._dibc / self._c

    @staticmethod
    def validate(a: Real,
                 b: Real,
                 c: Real,
                 d: Real):
        qt_require(c > 0, f"c ({c}) must be positive")
        qt_require(d >= 0, f"d ({d}) must be non negative")
        qt_require(a + d >= 0, f"a+d ({a + d}) must be non negative")

        if b >= 0.0:
            return

        # the one and only stationary point...
        zero_first_derivative = 1.0 / c - a / b
        if zero_first_derivative >= 0.0:
            # ... is a minimum
            # must be abcd(zero_first_derivative)>=0
            qt_require(b >= -(d * c) / math.exp(c * a / b - 1.0),
                       f"b ({b}) less than {-(d * c) / math.exp(c * a / b - 1.0)}: negative function value at stationary point {zero_first_derivative}")

    def __call__(self, t: Real):
        return 0.0 if t < 0 else (self._a + self._b * t) * math.exp(-self._c * t) + self._d

    def derivative(self, t: Real):
        return 0.0 if t < 0 else (self._da + self._db * t) * math.exp(-self._c * t)

    def primitive(self, t: Real):
        return 0.0 if t < 0 else (self._pa + self._pb * t) * math.exp(-self._c * t) + self._d * t + self._K

    def maximum_value(self):
        if self._b == 0.0 or self._a <= 0.0:
            return self._d
        return self(self.maximum_location())

    def maximum_location(self):
        """ time at which the function reaches maximum (if any) """
        if self._b == 0.0:
            if self._a >= 0.0:
                return 0.0
            else:
                return sys.float_info.max

        # stationary point
        # TODO check if minimum
        # TODO check if maximum at +inf
        zero_first_derivative = 1.0 / self._c - self._a / self._b
        return zero_first_derivative if zero_first_derivative > 0.0 else 0.0

    def long_term_value(self):
        return self._d

    def definite_integral(self, t1: Real, t2: Real):
        return self.primitive(t2) - self.primitive(t1)

    def a(self):
        return self._a

    def b(self):
        return self._b

    def c(self):
        return self._c

    def d(self):
        return self._d

    def coefficients(self):
        return self._abcd

    def derivative_coefficients(self):
        return self._dabcd

    def definite_integral_coefficients(self, t: Real, t2: Real):
        dt = t2 - t
        expcdt = math.exp(-self._c * dt)
        result = [None] * 4
        result[0] = self._diacplusbcc - (self._diacplusbcc + self._dibc * dt) * expcdt
        result[1] = self._dibc * (1.0 - expcdt)
        result[2] = self._c
        result[3] = self._d * dt
        return result

    def definite_derivative_coefficients(self, t: Real, t2: Real):
        dt = t2 - t
        expcdt = math.exp(-self._c * dt)
        result: List[Optional[Real]] = [None] * 4
        result[1] = self._b * self._c / (1.0 - expcdt)
        result[0] = self._a * self._c - self._b + result[1] * dt * expcdt
        result[0] /= 1.0 - expcdt
        result[2] = self._c
        result[3] = self._d / dt
        return result
