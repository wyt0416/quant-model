from qtmodel.error import qt_require
from qtmodel.timegrid import TimeGrid


class Path:
    """
    single-factor random walk
    the path includes the initial asset value as its first point.
    """

    def __init__(self, time_grid: TimeGrid, values: list = None):
        self._time_grid = time_grid
        self._values = values
        if self._values is None:
            self._values = [None] * self._time_grid.size()
        qt_require(len(self._values) == self._time_grid.size(),
                   "different number of times and asset values")

    def empty(self):
        return self._time_grid.empty()

    def length(self):
        return self._time_grid.size()

    def value(self, i: int):
        return self._values[i]

    def time(self, i: int):
        return self._time_grid[i]

    def time_grid(self):
        return self._time_grid

    def __getitem__(self, item):
        return self._values[item]
