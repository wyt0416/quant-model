from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.triplebandlinearop import TripleBandLinearOp


class SecondDerivativeOp(TripleBandLinearOp):

    def __init__(self,
                 direction: int,
                 mesher: FdmMesher):
        super(SecondDerivativeOp, self).__init__(direction, mesher)

        layout = mesher.layout()
        end_iter = layout.end()

        iter = layout.begin()
        while iter != end_iter:
            i = iter.index()
            hm = mesher.dminus(iter, self._direction)
            hp = mesher.dplus(iter, self._direction)

            zetam1 = hm * (hm + hp)
            zeta0 = hm * hp
            zetap1 = hp * (hm + hp)

            co = iter.coordinates()[self._direction]
            if co == 0 or co == layout.dim()[direction] - 1:
                self._lower[i] = self._diag[i] = self._upper[i] = 0.0
            else:
                self._lower[i] = 2.0 / zetam1
                self._diag[i] = -2.0 / zeta0
                self._upper[i] = 2.0 / zetap1

            iter.increment()
