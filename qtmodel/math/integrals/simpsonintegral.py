from typing import Callable

from qtmodel.error import QTError
from qtmodel.math.integrals.trapezoidintegral import TrapezoidIntegral, Default
from qtmodel.types import Real


class SimpsonIntegral(TrapezoidIntegral):
    """ Integral of a one-dimensional function """

    def __init__(self, accuracy: Real, max_iterations: int):
        super().__init__(accuracy, max_iterations, Default)

    def integrate(self,
                  f: Callable[[float], float],
                  a: Real,
                  b: Real):
        # start from the coarsest trapezoid...
        N = 1
        I = (f(a) + f(b)) * (b - a) / 2.0
        adjI = I
        # ...and refine it
        i = 1

        newI = Default.integrate(f, a, b, I, N)
        N *= 2
        newAdjI = (4.0 * newI - I) / 3.0
        # good enough? Also, don't run away immediately
        if abs(adjI - newAdjI) <= self.absolute_accuracy() and i > 5:
            # ok, exit
            return newAdjI
        # oh well. Another step.
        I = newI
        adjI = newAdjI
        i += 1
        while i < self.max_evaluations():
            newI = Default.integrate(f, a, b, I, N)
            N *= 2
            newAdjI = (4.0 * newI - I) / 3.0
            # good enough? Also, don't run away immediately
            if abs(adjI - newAdjI) <= self.absolute_accuracy() and i > 5:
                # ok, exit
                return newAdjI
            # oh well. Another step.
            I = newI
            adjI = newAdjI
            i += 1

        QTError("max number of iterations reached")
