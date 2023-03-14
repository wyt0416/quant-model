from typing import List, Optional

from qtmodel.math.interpolation import Interpolation, InterpolationTemplateImpl
from qtmodel.types import Real


class LinearInterpolationImpl(InterpolationTemplateImpl):
    def __init__(self, x: list, y: list):
        super(LinearInterpolationImpl, self).__init__(x, y, Linear.required_points)
        _x_len = len(x)
        self._primitive_const: List[Optional[Real]] = [None] * _x_len
        self._s: List[Optional[Real]] = [None] * _x_len

    def update(self):
        self._primitive_const[0] = 0.0
        _x_len = len(self._x)
        for i in range(1, _x_len):
            dx = self._x[i] - self._x[i-1]
            self._s[i-1] = (self._y[i]-self._y[i-1])/dx
            self._primitive_const[i] = self._primitive_const[i - 1] + dx * (self._y[i-1] +0.5 * dx * self._s[i-1])

    def value(self, x: Real):
        i = self.locate(x)
        return self._y[i] + (x - self._x[i]) * self._s[i]

    def primitive(self, x: Real):
        i = self.locate(x)
        dx = x - self._x[i]
        return self._primitive_const[i] + dx * (self._y[i] + 0.5 * dx * self._s[i])

    def derivative(self, x: Real):
        i = self.locate(x)
        return self._s[i]

    def second_derivative(self, x: Real):
        return 0.0


class LinearInterpolation(Interpolation):
    """ Linear interpolation between discrete points """

    def __init__(self, x: list, y: list):
        super().__init__()
        self._impl = LinearInterpolationImpl(x, y)
        self._impl.update()


class Linear:
    """ Linear-interpolation factory and traits """

    lglobal = False
    required_points = 2

    @staticmethod
    def interpolate(x, y):
        return LinearInterpolation(x, y)
