from typing import List


class FdmLinearOpIterator:

    def __init__(self, dim: List[int] = None, coordinates: List[int] = None, index: int = 0):
        self._index = None
        self._dim = None
        self._coordinates = None
        if dim is not None and coordinates is not None:
            self._index = index
            self._dim = dim
            self._coordinates = coordinates
        elif dim is not None:
            self._index = index
            self._dim = dim
            self._coordinates = [0] * len(dim)
        else:
            self._index = index

    def increment(self):
        self._index += 1
        i = 0
        while i < len(self._dim):
            self._coordinates[i] += 1
            if self._coordinates == self._dim[i]:
                self._coordinates[i] = 0
            else:
                break
            i += 1

    def __ne__(self, other):
        """ self!=other. """
        return self._index != other._index

    def index(self):
        return self._index

    def coordinates(self):
        return self._coordinates

    def swap(self, iter):
        iter._index, self._index = self._index, iter._index
        iter._dim, self._dim = self._dim, iter._dim
        iter._coordinates, self._coordinates = self._coordinates, iter._coordinates
