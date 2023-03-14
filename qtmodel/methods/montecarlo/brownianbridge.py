import math
from typing import List, Optional

from qtmodel.error import QTError, qt_require
from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class BrownianBridge:
    """
    Builds Wiener process paths using Gaussian variates
    This class generates normalized (i.e., unit-variance) paths as
    sequences of variations. In order to obtain the actual path of
    the underlying, the returned variations must be multiplied by
    the integrated variance (including time) over the
    corresponding time step.
    """

    def __init__(self,
                 steps: int = None,
                 times: List[Real] = None,
                 time_grid: TimeGrid = None):
        # The constructor generates the time grid so that each step
        # is of unit-time length.
        # steps: The number of steps in the path.
        if steps is not None:
            self._size = steps
            self._t: List[Optional[Real]] = [None] * self._size
            self._sqrtdt: List[Optional[Real]] = [None] * self._size
            self._bridge_index: List[Optional[int]] = [None] * self._size
            self._left_index: List[Optional[int]] = [None] * self._size
            self._right_index: List[Optional[int]] = [None] * self._size
            self._left_weight: List[Optional[Real]] = [None] * self._size
            self._right_weight: List[Optional[Real]] = [None] * self._size
            self._std_dev: List[Optional[Real]] = [None] * self._size
            for i in range(self._size):
                self._t[i] = i + 1
            self.initialize()
        # The step times are copied from the supplied vector
        # times: A vector containing the times at which the
        # steps occur. This also defines the number of
        # steps that will be generated.
        elif times is not None:
            self._size = len(times)
            self._t: List[Optional[Real]] = times
            self._sqrtdt: List[Optional[Real]] = [None] * self._size
            self._bridge_index: List[Optional[int]] = [None] * self._size
            self._left_index: List[Optional[int]] = [None] * self._size
            self._right_index: List[Optional[int]] = [None] * self._size
            self._left_weight: List[Optional[Real]] = [None] * self._size
            self._right_weight: List[Optional[Real]] = [None] * self._size
            self._std_dev: List[Optional[Real]] = [None] * self._size
            self.initialize()
        # The step times are copied from the TimeGrid object
        # time_grid: a time grid containing the times at
        # which the steps will occur
        elif time_grid is not None:
            self._size = time_grid.size() - 1
            self._t: List[Optional[Real]] = [None] * self._size
            self._sqrtdt: List[Optional[Real]] = [None] * self._size
            self._bridge_index: List[Optional[int]] = [None] * self._size
            self._left_index: List[Optional[int]] = [None] * self._size
            self._right_index: List[Optional[int]] = [None] * self._size
            self._left_weight: List[Optional[Real]] = [None] * self._size
            self._right_weight: List[Optional[Real]] = [None] * self._size
            self._std_dev: List[Optional[Real]] = [None] * self._size
            for i in range(self._size):
                self._t[i] = time_grid[i + 1]
            self.initialize()
        else:
            raise QTError("it's not in the three scenarios")

    def initialize(self):
        self._sqrtdt[0] = math.sqrt(self._t[0])
        for i in range(1, self._size):
            self._sqrtdt[i] = math.sqrt(self._t[i] - self._t[i - 1])

        # map_ is used to indicate which points are already constructed.
        # If map_[i] is zero, path point i is yet unconstructed.
        # map_[i]-1 is the index of the variate that constructs
        # the path point # i.
        map_ = [0] * self._size

        #  The first point in the construction is the global step.
        map_[self._size - 1] = 1
        #  The global step is constructed from the first variate.
        self._bridge_index[0] = self._size - 1
        #  The variance of the global step
        self._std_dev[0] = math.sqrt(self._t[self._size - 1])
        #  The global step to the last point in time is special.
        self._left_weight[0] = self._right_weight[0] = 0.0

        j = 0
        for i in range(1, self._size):
            # Find the next unpopulated entry in the map_.
            while map_[j] != 0:
                j += 1
            k = j
            # Find the next populated entry in the map_ from there.
            while map_[k] == 0:
                k += 1
            # l-1 is now the index of the point to be constructed next.
            l = j + ((k - 1 - j) >> 1)
            map_[l] = i
            # The i-th Gaussian variate will be used to set point l-1.
            self._bridge_index[i] = l
            self._left_index[i] = j
            self._right_index[i] = k
            if j != 0:
                self._left_weight[i] = (self._t[k] - self._t[l]) / (self._t[k] - self._t[j - 1])
                self._right_weight[i] = (self._t[l] - self._t[j - 1]) / (self._t[k] - self._t[j - 1])
                self._std_dev[i] = math.sqrt(
                    ((self._t[l] - self._t[j - 1]) * (self._t[k] - self._t[l])) / (self._t[k] - self._t[j - 1]))
            else:
                self._left_weight[i] = (self._t[k] - self._t[l]) / self._t[k]
                self._right_weight[i] = self._t[l] / self._t[k]
                self._std_dev[i] = math.sqrt(self._t[l] * (self._t[k] - self._t[l]) / self._t[k])

            j = k + 1
            if j >= self._size:
                j = 0  # wrap around

    def size(self):
        return self._size

    def times(self):
        return self._t

    def bridge_index(self):
        return self._bridge_index

    def left_index(self):
        return self._left_index

    def right_index(self):
        return self._right_index

    def left_weight(self):
        return self._left_weight

    def right_weight(self):
        return self._right_weight

    def std_deviation(self):
        return self._std_dev

    def transform(self, input: list, output: list):
        qt_require(len(input) == self._size,
                   "incompatible sequence size")
        # We use output to store the path...
        output[self._size - 1] = self._std_dev[0] * input[0]
        for i in range(1, self._size):
            j = self._left_index[i]
            k = self._right_index[i]
            l = self._bridge_index[i]
            if j != 0:
                output[l] = self._left_weight[i] * output[j - 1] + self._right_weight[i] * output[k] + self._std_dev[
                    i] * input[i]
            else:
                output[l] = self._right_weight[i] * output[k] + self._std_dev[i] * input[i]

        # ...after which, we calculate the variations and
        # normalize to unit times
        for i in range(self._size - 1, 0, -1):
            output[i] -= output[i - 1]
            output[i] /= self._sqrtdt[i]
        output[0] /= self._sqrtdt[0]

