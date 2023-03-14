"""
References: J-P. Berrut and L.N. Trefethen,
            Barycentric Lagrange interpolation,
            SIAM Review, 46(3):501–517, 2004.
https://people.maths.ox.ac.uk/trefethen/barycentric.pdf
"""
from abc import ABCMeta, abstractmethod
from typing import List, Optional

from qtmodel.error import qt_require, QTError
from qtmodel.math.comparison import close_enough
from qtmodel.math.interpolation import InterpolationTemplateImpl, Interpolation
from qtmodel.types import Real


class UpdatedYInterpolation(metaclass=ABCMeta):

    @abstractmethod
    def value(self, y_values: list, x: Real):
        pass


class LagrangeInterpolationImpl(InterpolationTemplateImpl, UpdatedYInterpolation):

    def __init__(self, x: list, y: list):
        InterpolationTemplateImpl.__init__(self, x, y)
        self._x = x
        self._y = y
        self._n = len(x)
        self._lambda: List[Optional[Real]] = [None] * self._n
        qt_require(len(set(x)) == self._n, "x values must not contain duplicates")

    def update(self):
        cM1 = 4.0 / (self._x[-1] - self._x[0])

        for i in range(self._n):
            self._lambda[i] = 1.0

            x_i = self._x[i]
            for j in range(self._n):
                if i != j:
                    self._lambda[i] *= cM1 * (x_i - self._x[j])
            self._lambda[i] = 1.0 / self._lambda[i]

    def value(self, x: Real, y: list = None):
        if y is None:
            return self._value(self._y, x)
        else:
            return self._value(y, x)

    def derivative(self, x: Real):
        n = 0.0
        d = 0.0
        nd = 0.0
        dd = 0.0
        for i in range(self._n):
            x_i = self._x[i]

            if close_enough(x, x_i):
                p = 0.0
                for j in range(self._n):
                    if i != j:
                        p += self._lambda[j] / (x - self._x[j])*(self._y[j] - self._y[i])
                return p / self._lambda[i]

            alpha = self._lambda[i] / (x - x_i)
            alphad = -alpha / (x - x_i)
            n += alpha * self._y[i]
            d += alpha
            nd += alphad * self._y[i]
            dd += alphad
        return (nd * d - n * dd) / (d * d)

    def primitive(self, x: Real):
        QTError("LagrangeInterpolation primitive is not implemented")

    def second_derivative(self, x: Real):
        QTError("LagrangeInterpolation secondDerivative is not implemented")

    def _value(self, y, x: Real):
        n = 0.0
        d = 0.0
        for i in range(self._n):
            x_i = self._x[i]
            if close_enough(x, x_i):
                return self._y[i]

            alpha = self._lambda[i] / (x - x_i)
            n += alpha * self._y[i]
            d += alpha
        return n / d


class LagrangeInterpolation(Interpolation):
    """
    See the Interpolation class for information about the
    required lifetime of the underlying data.
    """
    def __init__(self, x: list, y: list):
        super(LagrangeInterpolation, self).__init__()
        self._impl = LagrangeInterpolationImpl(x, y)
        self._impl.update()

    def value(self, y: list, x: Real):
        """
        interpolate with new set of y values for a new x value
        :param y:
        :param x:
        :return:
        """
        return self._impl.value(x, y)
