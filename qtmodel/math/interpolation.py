import bisect
from abc import ABCMeta, abstractmethod
from typing import List, Optional

from qtmodel.error import qt_require
from qtmodel.math.comparison import close
from qtmodel.math.interpolations.extrapolation import Extrapolator
from qtmodel.types import Real


class InterpolationImpl(metaclass=ABCMeta):
    """ abstract base class for interpolation implementations """

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def x_min(self) -> Real:
        pass

    @abstractmethod
    def x_max(self) -> Real:
        pass

    @abstractmethod
    def x_values(self) -> List[Real]:
        pass

    @abstractmethod
    def y_values(self) -> List[Real]:
        pass

    @abstractmethod
    def is_in_range(self, x: Real) -> bool:
        pass

    @abstractmethod
    def value(self, x: Real) -> Real:
        pass

    @abstractmethod
    def primitive(self, x: Real) -> Real:
        pass

    @abstractmethod
    def derivative(self, x: Real) -> Real:
        pass

    @abstractmethod
    def second_derivative(self, x: Real) -> Real:
        pass


class InterpolationTemplateImpl(InterpolationImpl, metaclass=ABCMeta):
    """ basic template implementation """

    def __init__(self,
                 x: list,
                 y: list,
                 required_points: int = 2):
        qt_require(len(x) >= required_points,
                   f"not enough points to interpolate: at least {required_points} required, {len(x)} provided")
        self._x = x
        self._y = y

    def x_min(self):
        return self._x[0]

    def x_max(self):
        return self._x[-1]

    def x_values(self):
        return list(self._x)

    def y_values(self):
        return list(self._y)

    def is_in_range(self, x):
        qt_require(self._x == sorted(self._x), "unsorted x values")

        x1 = self.x_min()
        x2 = self.x_max()
        return (x1 <= x <= x2) or close(x, x1) or close(x, x2)

    def locate(self, x: Real):
        qt_require(self._x == sorted(self._x), "unsorted x values")
        if x < self.x_min():
            return 0
        elif x > self.x_max():
            return len(self._x) - 2
        else:
            return bisect.bisect_right(self._x[:-1], x) - 1


class Interpolation(Extrapolator):
    """
    base class for 1-D interpolations.
    Classes derived from this class will provide interpolated
    values from two sequences of equal length, representing
    discretized values of a variable and a function of the former,
    respectively.
    """

    def __init__(self):
        super(Interpolation, self).__init__()
        self._impl: Optional[InterpolationImpl] = None

    def empty(self) -> bool:
        return self._impl is None

    def __call__(self, x: Real, allow_extrapolation: bool = False):
        self.check_range(x, allow_extrapolation)
        return self._impl.value(x)

    def check_range(self, x: Real, extrapolate: bool = False):
        qt_require(extrapolate or self.allows_extrapolation() or self._impl.is_in_range(x),
                   f"interpolation range is [{self._impl.x_min()}, {self._impl.x_max()}]: extrapolation at {x} not allowed")

    def primitive(self, x: Real, allow_extrapolation: bool = False):
        self.check_range(x, allow_extrapolation)
        return self._impl.primitive(x)

    def derivative(self, x: Real, allow_extrapolation: bool = False):
        self.check_range(x, allow_extrapolation)
        return self._impl.derivative(x)

    def second_derivative(self, x: Real, allow_extrapolation: bool = False):
        self.check_range(x, allow_extrapolation)
        return self._impl.second_derivative(x)

    def x_min(self):
        return self._impl.x_min()

    def x_max(self):
        return self._impl.x_max()

    def is_in_range(self, x: Real):
        return self._impl.is_in_range(x)

    def update(self):
        self._impl.update()
