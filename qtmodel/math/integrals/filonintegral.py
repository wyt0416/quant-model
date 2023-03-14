import math
import sys
from enum import Enum
from typing import Callable, Union

from qtmodel.error import qt_require, QTError
from qtmodel.math.array import generate_array
from qtmodel.math.integrals.integral import Integrator


class FilonIntegralTypes(Enum):
    Sine = "Sine"
    Cosine = "Cosine"


class FilonIntegral(Integrator):
    """
    References:
    Abramowitz, M. and Stegun, I. A. (Eds.).
    Handbook of Mathematical Functions with Formulas, Graphs,
    and Mathematical Tables, 9th printing. New York: Dover,
    pp. 890-891, 1972.
    """
    def __init__(self,
                 type: FilonIntegralTypes,
                 t: Union[float, int],
                 intervals: int):
        qt_require(not (intervals & 1), "number of intervals must be even")
        super().__init__(sys.float_info.max, intervals+1)
        self._type = type
        self._t = t
        self._intervals = intervals
        self._n = int(intervals / 2)

    def integrate(self, f: Callable[[float], float], a, b):
        h = (b - a) / (2 * self._n)
        x = generate_array(2 * self._n + 1, a, h)

        theta = self._t * h
        theta2 = theta * theta
        theta3 = theta2 * theta

        alpha = 1 / theta + math.sin(2 * theta) / (2 * theta2) - 2 * math.sin(theta)**2 / theta3
        beta = 2 * ((1 + math.cos(theta) ** 2) / theta2 - math.sin(2 * theta) / theta3)
        gamma = 4 * (math.sin(theta) / theta3 - math.cos(theta) / theta2)

        v = list(map(f, x))

        f1 = None
        f2 = None
        if self._type == FilonIntegralTypes.Cosine:
            f1 = math.sin
            f2 = math.cos

        elif self._type == FilonIntegralTypes.Sine:
            f1 = math.cos
            f2 = math.sin

        else:
            QTError("unknown integration type")

        c_2n_1 = 0.0
        c_2n = v[0] * f2(self._t * a) - 0.5 * (v[2 * self._n] * f2(self._t * b) + v[0] * f2(self._t * a))

        for i in range(1, self._n + 1):
            c_2n += v[2 * i] * f2(self._t * x[2 * i])
            c_2n_1 += v[2 * i - 1] * f2(self._t * x[2 * i - 1])

        return h * (alpha * (v[2 * self._n] * f1(self._t * x[2 * self._n]) - v[0] * f1(self._t * x[0])) * (
            1.0 if self._type == FilonIntegralTypes.Cosine else -1.0) + beta * c_2n + gamma * c_2n_1)

