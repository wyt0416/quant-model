import math
import sys

import numpy as np

from qtmodel.error import qt_require, QTError
from qtmodel.types import Real


class FiniteDifferenceModel:
    """
    Generic finite difference model
    """

    def __init__(self,
                 Evolver=None,
                 L=None,
                 bcs=None,
                 evolver=None,
                 stopping_times: list = None):
        if evolver is not None:
            self._evolver = evolver
        elif Evolver is not None and L is not None and bcs is not None:
            self._evolver = Evolver(L, bcs)
        else:
            raise QTError("it's not in the two scenarios")
        self._stopping_times = stopping_times
        tmp = np.unique(self._stopping_times)
        self._stopping_times.clear()
        self._stopping_times.extend(tmp)

    def evolver(self):
        return self._evolver

    def rollback(self, a, begin: Real, end: Real, steps: int, condition=None):
        return self._rollback_impl(a, begin, end, steps, condition)

    # solves the problem between the given times, applying a condition at every step.
    def _rollback_impl(self, a, begin: Real, end: Real, steps: int, condition=None):

        qt_require(begin >= end, f"trying to roll back from {begin} to {end}")

        dt = (begin - end) / steps
        t = begin
        self._evolver.set_step(dt)

        if self._stopping_times is not None and self._stopping_times[-1] == begin:
            if condition is not None:
                condition.apply_to(a, begin)
        i = 0
        while i < steps:
            now = t
            # make sure last step ends exactly on "to" in order to not
            # miss a stopping time at "to" due to numerical issues
            next_ = t - dt if (i < steps - 1) else end

            if abs(end - next_) < math.sqrt(sys.float_info.epsilon):
                next_ = end
            hit = False
            for j in range(len(self._stopping_times) - 1, -1, -1):
                if next_ <= self._stopping_times[j] < now:
                    # a stopping time was hit
                    hit = True

                    # perform a small step to stoppingTimes_[j]...
                    self._evolver.set_step(now - self._stopping_times[j])
                    self._evolver.step(a, now)
                    if condition is not None:
                        condition.apply_to(a, self._stopping_times[j])
                    # ...and continue the cycle
                    now = self._stopping_times[j]
            # if we did hit...
            if hit:
                # ...we might have to make a small step to
                # complete the big one...
                if now > next_:
                    self._evolver.set_step(now - next_)
                    self._evolver.step(a, now)
                    if condition is not None:
                        condition.apply_to(a, next_)
                # ...and in any case, we have to reset the
                # evolver to the default step.
                self._evolver.set_step(dt)
            else:
                # if we didn't, the evolver is already set to the
                # default step, which is ok for us.
                self._evolver.step(a, now)
                if condition is not None:
                    condition.apply_to(a, next_)
            i += 1
            t -= dt
