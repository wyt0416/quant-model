import numpy as np

from qtmodel.math.interpolations.interpolation2d import Interpolation2DTemplateImpl, Interpolation2D
from qtmodel.types import Real


class BilinearInterpolationImpl(Interpolation2DTemplateImpl):

    def __init__(self, x: list, y: list, z_data: np.ndarray):
        super(BilinearInterpolationImpl, self).__init__(x, y, z_data)
        self.calculate()

    def calculate(self):
        pass

    def value(self, x: Real, y: Real):
        i = self.locate_x(x)
        j = self.locate_y(y)

        z1 = self._z_data[j, i]
        z2 = self._z_data[j, i + 1]
        z3 = self._z_data[j + 1, i]
        z4 = self._z_data[j + 1, i + 1]

        t = (x - self._x[i]) / (self._x[i + 1] - self._x[i])
        u = (y - self._y[j]) / (self._y[j + 1] - self._y[j])

        return (1.0 - t) * (1.0 - u) * z1 + t * (1.0 - u) * z2 + (1.0 - t) * u * z3 + t * u * z4


class BilinearInterpolation(Interpolation2D):
    """ bilinear interpolation between discrete points """

    def __init__(self, x: list, y: list, z_data: np.ndarray):
        super(BilinearInterpolation, self).__init__()
        self._impl = BilinearInterpolationImpl(x, y, z_data)


class Bilinear:
    """ bilinear-interpolation factory """

    def interpolate(self, x: list, y: list, z: np.ndarray):
        return BilinearInterpolation(x, y, z)
