from typing import List, Optional

import numpy as np

from qtmodel.methods.finitedifferences.operators.fdmlinearopiterator import FdmLinearOpIterator


class FdmLinearOpLayout:
    def __init__(self, dim: List):
        self._dim = dim
        self._spacing: List[Optional[int]] = [None] * len(self._dim)
        self._spacing[0] = 1
        for i in range(len(self._dim) - 1):
            self._spacing[i + 1] = np.prod(self._dim[:i + 1])
        self._size = self._spacing[-1] * dim[-1]

    def begin(self):
        return FdmLinearOpIterator(dim=self._dim)

    def end(self):
        return FdmLinearOpIterator(index=self._size)

    def dim(self):
        return self._dim

    def spacing(self):
        return self._spacing

    def size(self):
        return self._size

    def index(self, coordinates: list):
        return sum(i * j for i, j in zip(coordinates, self._spacing[:len(coordinates)]))

    def neighbourhood(self,
                      iterator: FdmLinearOpIterator,
                      i1: int,
                      offset1: int,
                      i2: int = None,
                      offset2: int = None):
        if i2 is None and offset2 is None:
            my_index = iterator.index() - iterator.coordinates()[i1] * self._spacing[i1]

            coor_offset = int(iterator.coordinates()[i1]) + offset1
            if coor_offset < 0:
                coor_offset = - coor_offset
            elif int(coor_offset) >= self._dim[i1]:
                coor_offset = 2 * (self._dim[i1] - 1) - coor_offset
            return my_index + coor_offset * self._spacing[i1]

        else:
            my_index = iterator.index() - iterator.coordinates()[i1] * self._spacing[i1] - iterator.coordinates()[i2] * \
                       self._spacing[i2]

            coor_offset_1 = int(iterator.coordinates()[i1]) + offset1
            if coor_offset_1 < 0:
                coor_offset_1 = -coor_offset_1
            elif int(coor_offset_1) >= self._dim[i1]:
                coor_offset_1 = 2 * (self._dim[i1] - 1) - coor_offset_1

            coor_offset_2 = int(iterator.coordinates()[i2]) + offset2
            if coor_offset_2 < 0:
                coor_offset_2 = -coor_offset_2
            elif int(coor_offset_2) >= self._dim[i2]:
                coor_offset_2 = 2 * (self._dim[i2] - 1) - coor_offset_2

            return my_index + coor_offset_1 * self._spacing[i1] + coor_offset_2 * self._spacing[i2]

    # smart but sometimes too slow
    def iter_neighbourhood(self, iterator, i: int, offset: int):

        coordinates = iterator.coordinates()

        coor_offset = int(coordinates[i]) + offset
        if coor_offset < 0:
            coor_offset = -coor_offset
        elif int(coor_offset) >= self._dim[i]:
            coor_offset = 2 * (self._dim[i] - 1) - coor_offset
        coordinates[i] = int(coor_offset)

        return FdmLinearOpIterator(self._dim, coordinates, self.index(coordinates))
