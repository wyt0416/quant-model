from abc import ABCMeta, abstractmethod
from typing import Optional

import numpy as np

from qtmodel.error import qt_require
from qtmodel.math.array import upper_bound
from qtmodel.math.comparison import close
from qtmodel.math.interpolations.extrapolation import Extrapolator
from qtmodel.types import Real


class Interpolation2DImpl(metaclass=ABCMeta):
    """ abstract base class for 2-D interpolation implementations """

    @abstractmethod
    def calculate(self):
        pass

    @abstractmethod
    def x_min(self):
        pass

    @abstractmethod
    def x_max(self):
        pass

    @abstractmethod
    def x_values(self):
        pass

    @abstractmethod
    def locate_x(self, x: Real):
        pass

    @abstractmethod
    def y_min(self):
        pass

    @abstractmethod
    def y_max(self):
        pass

    @abstractmethod
    def y_values(self):
        pass

    @abstractmethod
    def locate_y(self, y: Real):
        pass

    @abstractmethod
    def z_data(self):
        pass

    @abstractmethod
    def is_in_range(self, x: Real, y: Real):
        pass

    @abstractmethod
    def value(self, x: Real, y: Real):
        pass


class Interpolation2DTemplateImpl(Interpolation2DImpl):
    """ basic template implementation """

    def __init__(self, x: list, y: list, z_data: np.ndarray):
        self._x = x
        self._y = y
        self._z_data = z_data
        qt_require(len(self._x) >= 2,
                   f"not enough x points to interpolate: at least 2 required, {len(self._x)} provided")
        qt_require(len(self._y) >= 2,
                   f"not enough y points to interpolate: at least 2 required, {len(self._y)} provided")

    def x_min(self):
        return self._x[0]

    def x_max(self):
        return self._x[-1]

    def x_values(self):
        return self._x

    def y_min(self):
        return self._y[0]

    def y_max(self):
        return self._y[-1]

    def y_values(self):
        return self._y

    def z_data(self):
        return self._z_data

    def is_in_range(self, x: Real, y: Real):
        qt_require(sorted(self._x) == self._x, "unsorted x values")

        x1 = self.x_min()
        x2 = self.x_max()
        x_is_inrange = (x1 <= x <= x2) or close(x, x1) or close(x, x2)
        if not x_is_inrange:
            return False

        qt_require(sorted(self._y) == self._y, "unsorted y values")

        y1 = self.y_min()
        y2 = self.y_max()
        return (y1 <= y <= y2) or close(y, y1) or close(y, y2)

    def locate_x(self, x: Real):
        qt_require(sorted(self._x) == self._x, "unsorted x values")
        if x < self._x[0]:
            return 0
        elif x > self._x[-1]:
            return len(self._x) - 2
        else:
            return upper_bound(self._x[:-1], x) - 1

    def locate_y(self, y: Real):
        qt_require(sorted(self._y) == self._y, "unsorted y values")
        if y < self._y[0]:
            return 0
        elif y > self._y[-1]:
            return len(self._y) - 2
        else:
            return upper_bound(self._y[:-1], y) - 1


class Interpolation2D(Extrapolator):
    """ base class for 2-D interpolations. """

    def __init__(self):
        super(Interpolation2D, self).__init__()
        self._impl: Optional[Interpolation2DImpl] = None

    def __call__(self, x: Real, y: Real, allow_extrapolation: bool = False):
        self.check_range(x, y, allow_extrapolation)
        return self._impl.value(x, y)

    def x_min(self):
        return self._impl.x_min()

    def x_max(self):
        return self._impl.x_max()

    def x_values(self):
        return self._impl.x_values()

    def locate_x(self, x: Real):
        return self._impl.locate_x(x)

    def y_min(self):
        return self._impl.y_min()

    def y_max(self):
        return self._impl.y_max()

    def y_values(self):
        return self._impl.y_values()

    def locate_y(self, y: Real):
        return self._impl.locate_y(y)

    def z_data(self):
        return self._impl.z_data()

    def is_in_range(self, x: Real, y: Real):
        return self._impl.is_in_range(x, y)

    def update(self):
        self._impl.calculate()

    def check_range(self, x: Real, y: Real, extrapolate: bool):
        qt_require(extrapolate or self.allows_extrapolation() or self._impl.is_in_range(x, y),
                   f"interpolation range is [{self._impl.x_min()}, {self._impl.x_max()}] "
                   f"x [{self._impl.y_min()}, {self._impl.y_max()}]: extrapolation at ({x}, {y}) not allowed")

