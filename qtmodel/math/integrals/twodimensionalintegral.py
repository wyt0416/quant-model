from typing import Callable, Tuple

from qtmodel.math.integrals.integral import Integrator
from qtmodel.types import Real


class TwoDimensionalIntegral:
    """ Integral of a two-dimensional function """

    def __init__(self, integrator_x: Integrator, integrator_y: Integrator):
        self._integrator_x = integrator_x
        self._integrator_y = integrator_y

    def __call__(self,
                 f: Callable[[float, float], float],
                 a: Tuple[float, float],
                 b: Tuple[float, float]):
        return self._integrator_x(lambda x: self.g(f, x, a[1], b[1]), a[0], b[0])

    def g(self,
          f: Callable[[float, float], float],
          x: Real,
          a: Real,
          b: Real):
        return self._integrator_y(lambda y: f(x, y), a, b)
