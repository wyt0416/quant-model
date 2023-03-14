from typing import List, Union

from qtmodel.error import qt_require, QTError
from qtmodel.methods.finitedifferences.meshers.fdm1dmesher import Fdm1dMesher
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.fdmlinearopiterator import FdmLinearOpIterator
from qtmodel.methods.finitedifferences.operators.fdmlinearoplayout import FdmLinearOpLayout


class FdmMesherComposite(FdmMesher):

    def __init__(self,
                 layout: FdmLinearOpLayout = None,
                 mesher: Union[List[Fdm1dMesher], Fdm1dMesher] = None,
                 m1: Fdm1dMesher = None,
                 m2: Fdm1dMesher = None,
                 m3: Fdm1dMesher = None,
                 m4: Fdm1dMesher = None):
        if layout is not None and isinstance(mesher, list):
            super(FdmMesherComposite, self).__init__(layout=layout)
            self._mesher = mesher
            for i in range(len(mesher)):
                qt_require(mesher[i].size() == layout.dim()[i],
                           f"size of 1d mesher {i} does not fit to layout")
        elif mesher is not None:
            if isinstance(mesher, list):
                super(FdmMesherComposite, self).__init__(self.get_layout_from_meshers(mesher))
                self._mesher = mesher
            elif isinstance(mesher, Fdm1dMesher):
                super(FdmMesherComposite, self).__init__(self.get_layout_from_meshers([mesher]))
                self._mesher = [mesher]
            else:
                raise QTError("mesher must be list or Fdm1dMesher")
        elif m1 is not None and m2 is not None:
            if m3 is not None and m4 is not None:
                super(FdmMesherComposite, self).__init__(self.get_layout_from_meshers([m1, m2, m3, m4]))
                self._mesher = [m1, m2, m3, m4]
            elif m3 is not None:
                super(FdmMesherComposite, self).__init__(self.get_layout_from_meshers([m1, m2, m3]))
                self._mesher = [m1, m2, m3]
            else:
                super(FdmMesherComposite, self).__init__(self.get_layout_from_meshers([m1, m2]))
                self._mesher = [m1, m2]
        else:
            raise QTError("it's not in the six scenarios")

    def dplus(self, iter: FdmLinearOpIterator, direction: int):
        return self._mesher[direction].dplus(iter.coordinates()[direction])

    def dminus(self, iter: FdmLinearOpIterator, direction: int):
        return self._mesher[direction].dminus(iter.coordinates()[direction])

    def location(self, iter: FdmLinearOpIterator, direction: int):
        return self._mesher[direction].location(iter.coordinates()[direction])

    def locations(self, direction: int):
        ret_val = [None] * self._layout.size()
        end_iter = self._layout.end()
        iter = self._layout.begin()
        while iter != end_iter:
            ret_val[iter.index()] = self._mesher[direction].locations()[iter.coordinates()[direction]]
            iter.increment()

        return ret_val

    def get_fdm1d_meshers(self):
        return self._mesher

    @staticmethod
    def get_layout_from_meshers(meshers: List[Fdm1dMesher]):
        dim = [None] * len(meshers)
        for i in range(len(dim)):
            dim[i] = meshers[i].size()
        return FdmLinearOpLayout(dim)
