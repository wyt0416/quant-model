from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.meshers.fdm1dmesher import Fdm1dMesher
from qtmodel.types import Real


class Uniform1dMesher(Fdm1dMesher):

    def __init__(self, start: Real, end: Real, size: int):
        super(Uniform1dMesher, self).__init__(size)
        qt_require(end > start, "end must be large than start")

        dx = (end - start) / (size - 1)

        for i in range(size - 1):
            self._locations[i] = start + i * dx
            self._dplus[i] = self._dminus[i + 1] = dx

        self._locations[-1] = end
        self._dplus[-1] = self._dminus[0] = None
