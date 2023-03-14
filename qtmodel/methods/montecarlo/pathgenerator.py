import copy

from qtmodel.error import qt_require, QTError
from qtmodel.methods.montecarlo.brownianbridge import BrownianBridge
from qtmodel.methods.montecarlo.path import Path
from qtmodel.methods.montecarlo.sample import Sample
from qtmodel.stochasticprocess import StochasticProcess
from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class PathGenerator:
    """
    Generates random paths using a sequence generator
    Generates random paths with drift(S,t) and variance(S,t)
    using a gaussian sequence generator
    """

    def __init__(self,
                 process: StochasticProcess,
                 generator,
                 brownian_bridge: bool,
                 length: Real = None,
                 time_steps: int = None,
                 time_grid: TimeGrid = None):
        self._brownian_bridge = brownian_bridge
        self._generator = generator
        self._dimension = self._generator.dimension()
        if length is not None and time_steps is not None:
            self._time_grid = TimeGrid(end=length, steps=time_steps)
            qt_require(self._dimension == time_steps,
                       f"sequence generator dimensionality ({self._dimension}) != timeSteps ({time_steps})")
        elif time_grid is not None:
            self._time_grid = time_grid
            qt_require(self._dimension == self._time_grid.size() - 1,
                       f"sequence generator dimensionality ({self._dimension}) != timeSteps ({self._time_grid.size() - 1})")
        else:
            raise QTError("it's not in the two scenarios")
        self._process = process
        self._next = Sample(Path(self._time_grid), 1.0)
        self._temp = [None] * self._dimension
        self._bb = BrownianBridge(time_grid=self._time_grid)

    def next(self, antithetic: bool = None):
        if antithetic is None:
            return self.next(False)
        else:
            sequence_ = self._generator.last_sequence() if antithetic else self._generator.next_sequence()

            if self._brownian_bridge:
                self._bb.transform(sequence_.value,
                                   self._temp)

            else:
                self._temp = copy.deepcopy(sequence_.value)

            self._next.weight = sequence_.weight

            path = self._next.value
            path[0] = self._process.x0()

            for i in range(1, path.length()):
                t = self._time_grid[i - 1]
                dt = self._time_grid.dt(i - 1)
                path[i] = self._process.evolve(t,
                                               path[i - 1],
                                               dt,
                                               -self._temp[i - 1] if antithetic else self._temp[i - 1])

            return self._next

    def antithetic(self):
        return self.next(True)

    def size(self):
        return self._dimension

    def time_grid(self):
        return self._time_grid
