import sys
from typing import Callable

from qtmodel.error import qt_require, QTError
from qtmodel.math.comparison import close

MAX_FUNCTION_EVALUATIONS = 100


class Solver1D:
    """ Base class for 1-D solvers """

    def __init__(self):
        self._root = None
        self._x_min = None
        self._x_max = None
        self._fx_min = None
        self._fx_max = None
        self._max_evaluations = MAX_FUNCTION_EVALUATIONS
        self._evaluation_number = None

        self._lower_bound = None
        self._upper_bound = None
        self._lower_bound_enforced = False
        self._upper_bound_enforced = False

    def solve(self,
              f: Callable,
              accuracy,
              guess,
              step=None,
              x_min=None,
              x_max=None):
        """
        x_min和x_max必须搭配传递，如果不传x_min和x_max，则必须要传step
        :param f:
        :param accuracy:
        :param guess:
        :param step:
        :param x_min:
        :param x_max:
        :return:
        """
        if step is not None:
            qt_require(accuracy > 0.0, f"accuracy ({accuracy}) must be positive")
            # check whether we really want to use epsilon
            accuracy = max(accuracy, sys.float_info.epsilon)

            growth_factor = 1.6
            flipflop = -1

            self._root = guess
            self._fx_max = f(self._root)

            # monotonically crescent bias, as in optionValue(volatility)
            if close(self._fx_max, 0.0):
                return self._root
            elif self._fx_max > 0.0:
                self._x_min = self.enforce_bounds(self._root - step)
                self._fx_min = f(self._x_min)
                self._x_max = self._root
            else:
                self._x_min = self._root
                self._fx_min = self._fx_max
                self._x_max = self.enforce_bounds(self._root + step)
                self._fx_max = f(self._x_max)

            self._evaluation_number = 2
            while self._evaluation_number <= self._max_evaluations:
                if self._fx_min * self._fx_max <= 0.0:
                    if close(self._fx_min, 0.0):
                        return self._x_min
                    if close(self._fx_max, 0.0):
                        return self._x_max
                    self._root = (self._x_max + self._x_min) / 2.0
                    return self.solve_impl(f, accuracy)

                if abs(self._fx_min) < abs(self._fx_max):
                    self._x_min = self.enforce_bounds(self._x_min + growth_factor * (self._x_min - self._x_max))
                    self._fx_min = f(self._x_min)
                elif abs(self._fx_min) > abs(self._fx_max):
                    self._x_max = self.enforce_bounds(self._x_max + growth_factor * (self._x_max - self._x_min))
                    self._fx_max = f(self._x_max)
                elif flipflop == -1:
                    self._x_min = self.enforce_bounds(self._x_min + growth_factor * (self._x_min - self._x_max))
                    self._fx_min = f(self._x_min)
                    self._evaluation_number += 1
                    flipflop = 1
                elif flipflop == 1:
                    self._x_max = self.enforce_bounds(self._x_max + growth_factor * (self._x_max - self._x_min))
                    self._fx_max = f(self._x_max)
                    flipflop = -1

                self._evaluation_number += 1

            QTError(f"unable to bracket root in {self._max_evaluations} "
                    f"function evaluations (last bracket attempt: "
                    f"f[{self._x_min}, {self._x_max}] "
                    f"-> [{self._fx_min},{self._fx_max}])")

        elif x_min is not None and x_max is not None:
            qt_require(accuracy > 0.0, f"accuracy ({accuracy}) must be positive")
            # check whether we really want to use epsilon
            accuracy = max(accuracy, sys.float_info.epsilon)

            self._x_min = x_min
            self._x_max = x_max

            qt_require(self._x_min < self._x_max, f"invalid range: _x_min ({self._x_min}) >= _x_max ({self._x_max})")
            qt_require(not self._lower_bound_enforced or self._x_min >= self._lower_bound,
                       f"_x_min ({self._x_min}) < enforced low bound ({self._lower_bound})")
            qt_require(not self._upper_bound_enforced or self._x_max <= self._upper_bound,
                       f"_x_max ({self._x_max}) > enforced hi bound ({self._upper_bound})")

            self._fx_min = f(self._x_min)
            if close(self._fx_min, 0.0):
                return self._x_min

            self._fx_max = f(self._x_max)
            if close(self._fx_max, 0.0):
                return self._x_max

            self._evaluation_number = 2

            qt_require(self._fx_min * self._fx_max < 0.0,
                       f"root not bracketed: f[{self._x_min}, {self._x_max}] -> [{self._fx_min}, {self._fx_max}]")

            qt_require(guess > self._x_min, f"guess ({guess}) < _x_min ({self._x_min})")
            qt_require(guess < self._x_max, f"guess ({guess}) > _x_max ({self._x_max})")

            self._root = guess

            return self.solve_impl(f, accuracy)

        else:
            raise QTError("x_min and x_max must be passed together. If they are not passed, step must be passed")

    def enforce_bounds(self, x):
        if self._lower_bound_enforced and x < self._lower_bound:
            return self._lower_bound
        if self._upper_bound_enforced and x > self._upper_bound:
            return self._upper_bound
        return x

    def set_max_evaluations(self, evaluations):
        """
        This method sets the maximum number of function evaluations
        for the bracketing routine. An error is thrown if a bracket
        is not found after this number of evaluations.
        """
        self._max_evaluations = evaluations

    def set_lower_bound(self, lower_bound):
        """ sets the lower bound for the function domain """
        self._lower_bound = lower_bound
        self._lower_bound_enforced = True

    def set_upper_bound(self, upper_bound):
        """ sets the upper bound for the function domain """
        self._upper_bound = upper_bound
        self._upper_bound_enforced = True
