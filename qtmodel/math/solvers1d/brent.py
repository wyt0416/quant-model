import sys
from typing import Callable

from qtmodel.error import QTError
from qtmodel.math.comparison import close
from qtmodel.math.solver1d import Solver1D


class Brent(Solver1D):
    """ Brent 1-D solver """

    def solve_impl(self, f: Callable, x_accuracy):
        """
        The implementation of the algorithm was inspired by
        Press, Teukolsky, Vetterling, and Flannery,
        "Numerical Recipes in C", 2nd edition, Cambridge
        University Press
        :param f:
        :param x_accuracy:
        :return:
        """
        # we want to start with root_ (which equals the guess) on
        # one side of the bracket and both _x_min and _x_max on the
        # other.
        froot = f(self._root)
        self._evaluation_number += 1
        if froot * self._fx_min < 0:
            self._x_max = self._x_min
            self._fx_max = self._fx_min
        else:
            self._x_min = self._x_max
            self._fx_min = self._fx_max

        d = self._root - self._x_max
        e = d

        while self._evaluation_number <= self._max_evaluations:
            if ((froot > 0.0 and self._fx_max > 0.0) or
                    (froot < 0.0 and self._fx_max < 0.0)):
                # Rename self._x_min, self._root, self._x_max and adjust bounds
                self._x_max = self._x_min
                self._fx_max = self._fx_min
                e = d = self._root - self._x_min

            if abs(self._fx_max) < abs(froot):
                self._x_min = self._root
                self._root = self._x_max
                self._x_max = self._x_min
                self._fx_min = froot
                froot = self._fx_max
                self._fx_max = self._fx_min

            # Convergence check
            x_acc1 = 2.0 * sys.float_info.epsilon * abs(self._root) + 0.5 * x_accuracy
            x_mid = (self._x_max - self._root) / 2.0
            if abs(x_mid) <= x_acc1 or (close(froot, 0.0)):
                f(self._root)
                self._evaluation_number += 1
                return self._root

            if (abs(e) >= x_acc1 and
                    abs(self._fx_min) > abs(froot)):

                # Attempt inverse quadratic interpolation
                s = froot / self._fx_min
                if close(self._x_min, self._x_max):
                    p = 2.0 * x_mid * s
                    q = 1.0 - s
                else:
                    q = self._fx_min / self._fx_max
                    r = froot / self._fx_max
                    p = s * (2.0 * x_mid * q * (q - r) - (self._root - self._x_min) * (r - 1.0))
                    q = (q - 1.0) * (r - 1.0) * (s - 1.0)

                if p > 0.0:
                    q = -q  # Check whether in bounds
                p = abs(p)
                min1 = 3.0 * x_mid * q - abs(x_acc1 * q)
                min2 = abs(e * q)
                if 2.0 * p < (min1 if min1 < min2 else min2):
                    e = d  # Accept interpolation
                    d = p / q
                else:
                    d = x_mid  # Interpolation failed, use bisection
                    e = d

            else:
                # Bounds decreasing too slowly, use bisection
                d = x_mid
                e = d

            self._x_min = self._root
            self._fx_min = froot
            if abs(d) > x_acc1:
                self._root += d
            else:
                self._root += self.sign(x_acc1, x_mid)
            froot = f(self._root)
            self._evaluation_number += 1

        QTError(f"maximum number of function evaluations ({self._max_evaluations}) exceeded")

    @staticmethod
    def sign(a, b):
        return abs(a) if b >= 0.0 else -abs(a)
