import copy

import numpy as np

from qtmodel.error import qt_require, QTError
from qtmodel.math.comparison import close_enough
from qtmodel.types import Real


class TimeGrid:
    """
    time grid class
    todo what was the rationale for limiting the grid to
         positive times? Investigate and see whether we
         can use it for negative ones as well.
    """

    def __init__(self,
                 end: Real = None,
                 steps: int = None,
                 iterator: list = None):
        if end is not None and steps is not None:
            # We seem to assume that the grid begins at 0.
            # Let's enforce the assumption for the time being
            # (even though I'm not sure that I agree.)
            qt_require(end > 0.0,
                       "negative times not allowed")
            dt = end / steps
            self._times = []
            for i in range(steps + 1):
                self._times.append(dt * i)

            self._mandatory_times = [end]

            self._dt = [dt] * steps
        elif iterator is not None and steps is not None:
            self._mandatory_times = copy.deepcopy(iterator)

            qt_require(len(iterator) > 0, "empty time sequence")
            self._mandatory_times.sort()
            # We seem to assume that the grid begins at 0.
            # Let's enforce the assumption for the time being
            # (even though I'm not sure that I agree.)
            qt_require(self._mandatory_times[0] >= 0.0,
                       "negative times not allowed")
            r = set()
            for i in range(len(self._mandatory_times)):
                for j in range(i + 1, len(self._mandatory_times)):
                    if close_enough(self._mandatory_times[i], self._mandatory_times[j]):
                        r.add(j)

            self._mandatory_times = [self._mandatory_times[i] for i in range(len(self._mandatory_times)) if i not in r]
            last = self._mandatory_times[-1]
            # The resulting timegrid have points at times listed in the input
            # list. Between these points, there are inner-points which are
            # regularly spaced.
            if steps == 0:
                diff = [self._mandatory_times[0]] + list(np.diff(self._mandatory_times))
                if diff[0] == 0.0:
                    diff.pop(0)
                dt_max = min(diff)
            else:
                dt_max = last / steps

            period_begin = 0.0
            self._times.append(period_begin)
            for t in self._mandatory_times:
                period_end = t
                if period_end != 0.0:
                    # the nearest integer, at least 1
                    n_steps = max(int(round((period_end - period_begin) / dt_max)), 1)
                    dt = (period_end - period_begin) / n_steps
                    for n in range(1, n_steps + 1):
                        self._times.append(period_begin + n * dt)
                period_begin = period_end

            self._dt = [self._times[1]] + list(np.diff(self._times[1:]))
        elif iterator is not None:
            self._mandatory_times = copy.deepcopy(iterator)

            qt_require(len(iterator) > 0, "empty time sequence")
            self._mandatory_times.sort()
            # We seem to assume that the grid begins at 0.
            # Let's enforce the assumption for the time being
            # (even though I'm not sure that I agree.)
            qt_require(self._mandatory_times[0] >= 0.0,
                       "negative times not allowed")
            r = set()
            for i in range(len(self._mandatory_times)):
                for j in range(i + 1, len(self._mandatory_times)):
                    if close_enough(self._mandatory_times[i], self._mandatory_times[j]):
                        r.add(j)

            self._mandatory_times = [self._mandatory_times[i] for i in range(len(self._mandatory_times)) if i not in r]

            if self._mandatory_times[0] > 0.0:
                self._times.append(0.0)

            self._times.extend(self._mandatory_times)

            self._dt = [self._times[1]] + list(np.diff(self._times[1:]))
        else:
            raise QTError("it's not in the three scenarios")

    def closest_index(self, t: Real):
        """ returns the index i such that grid[i] is closest to t """
        result = 0
        if t > max(self._times):
            return len(self._times) - 1

        for result in range(len(self._times)):
            if self._times[result] >= t:
                break
        if result == 0:
            return result
        else:
            dt1 = self._times[result] - t
            dt2 = t - self._times[result - 1]
            if dt1 < dt2:
                return result
            else:
                return result - 1

    def index(self, t: Real):
        """ returns the index i such that grid[i] = t """
        i = self.closest_index(t)
        if close_enough(t, self._times[i]):
            return i
        else:
            if t < self._times[0]:
                QTError(f"using inadequate time grid: all nodes are later than "
                        f"the required time t = {t:.12f} (earliest node is t1 = {self._times[0]:.12f})")
            elif t > self._times[-1]:
                QTError(f"using inadequate time grid: all nodes are earlier than the "
                        f"required time t = {t:.12f} (latest node is t1 = {self._times[-1]:.12f})")
            else:
                if t > self._times[i]:
                    j = i
                    k = i + 1
                else:
                    j = i - 1
                    k = i
                QTError(f"using inadequate time grid: the nodes closest to the required "
                        f"time t = {t:.12f} are t1 = {self._times[j]:.12f} and t2 = {self._times[k]:.12f}")

    def closest_time(self, t: Real):
        """ returns the time on the grid closest to the given t """
        return self._times[self.closest_index(t)]

    def mandatory_times(self):
        return self._mandatory_times

    def dt(self, i: int):
        return self._dt[i]

    def __getitem__(self, item):
        return self._times[item]

    def size(self):
        return len(self._times)

    def empty(self):
        return len(self._times) == 0
