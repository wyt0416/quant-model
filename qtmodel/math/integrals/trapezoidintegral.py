from typing import Callable

from qtmodel.error import QTError
from qtmodel.math.integrals.integral import Integrator
from qtmodel.types import Real


class TrapezoidIntegral(Integrator):
    """"""

    def __init__(self, accuracy: Real, max_iterations: int, integration_policy):
        super().__init__(accuracy, max_iterations)
        self._integration_policy = integration_policy

    def integrate(self,
                  f: Callable[[float], float],
                  a: Real,
                  b: Real):
        # start from the coarsest trapezoid...
        N = 1
        I = (f(a) + f(b)) * (b - a) / 2.0
        # ...and refine it
        i = 1

        newI = self._integration_policy.integrate(f, a, b, I, N)
        N *= self._integration_policy.nbEvalutions()
        # good enough? Also, don't run away immediately
        if abs(I - newI) <= self.absolute_accuracy() and i > 5:
            # ok, exit
            return newI
        # oh well. Another step.
        I = newI
        i += 1
        while i < self.max_evaluations():
            newI = self._integration_policy.integrate(f, a, b, I, N)
            N *= self._integration_policy.nbEvalutions()
            # good enough? Also, don't run away immediately
            if abs(I - newI) <= self.absolute_accuracy() and i > 5:
                # ok, exit
                return newI
            # oh well. Another step.
            I = newI
            i += 1

        QTError("max number of iterations reached")


class Default:
    """ Integration policies """

    @staticmethod
    def integrate(f: Callable[[float], float],
                  a: Real,
                  b: Real,
                  I: Real,
                  N: int):
        sum = 0.0
        dx = (b - a) / N
        x = a + dx / 2.0

        i = 0
        while i < N:
            sum += f(x)
            x += dx
            i += 1

        return (I + dx * sum) / 2.0

    @staticmethod
    def nb_evalutions():
        return 2


class MidPoint:

    @staticmethod
    def integrate(f: Callable[[float], float],
                  a: Real,
                  b: Real,
                  I: Real,
                  N: int):
        sum = 0.0
        dx = (b - a) / N
        x = a + dx / 6.0
        D = 2.0 * dx / 3.0

        i = 0
        while i < N:
            sum += f(x) + f(x + D)
            x += dx
            i += 1
        return (I + dx * sum) / 3.0

    @staticmethod
    def nb_evalutions():
        return 3
