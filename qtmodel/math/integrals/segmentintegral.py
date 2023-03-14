from typing import Callable

from qtmodel.error import qt_require
from qtmodel.math.comparison import close_enough
from qtmodel.math.integrals.integral import Integrator
from qtmodel.types import Real


class SegmentIntegral(Integrator):
    """ Integral of a one-dimensional function """

    def __init__(self, intervals: int):
        qt_require(intervals > 0, "at least 1 interval needed, 0 given")
        super().__init__(1, 1)
        self._intervals = intervals

    def integrate(self,
                  f: Callable[[float], float],
                  a: Real,
                  b: Real):
        if close_enough(a, b):
            return 0.0
        dx = (b - a) / self._intervals
        sum = 0.5 * (f(a) + f(b))
        end = b - 0.5 * dx
        x = a + dx
        while x < end:
            sum += f(x)
            x += dx
        return sum * dx
