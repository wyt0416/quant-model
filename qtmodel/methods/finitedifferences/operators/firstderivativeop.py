from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.triplebandlinearop import TripleBandLinearOp


class FirstDerivativeOp(TripleBandLinearOp):

    def __init__(self,
                 direction: int,
                 mesher: FdmMesher):
        super(FirstDerivativeOp, self).__init__(direction, mesher)

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

            if iter.coordinates()[self._direction] == 0:
                # upwinding scheme
                self._lower[i] = 0.0
                self._upper[i] = 1 / hp
                self._diag[i] = -self._upper[i]

            elif iter.coordinates()[self._direction] == layout.dim()[direction] - 1:
                # downwinding scheme
                self._diag[i] = 1 / hm
                self._lower[i] = -self._diag[i]
                self._upper[i] = 0.0

            else:
                self._lower[i] = -hp / zetam1
                self._diag[i] = (hp - hm) / zeta0
                self._upper[i] = hm / zetap1

            iter.increment()
