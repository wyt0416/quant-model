import math

from qtmodel.compounding import Compounding
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.operators.firstderivativeop import FirstDerivativeOp
from qtmodel.methods.finitedifferences.operators.secondderivativeop import SecondDerivativeOp
from qtmodel.methods.finitedifferences.operators.triplebandlinearop import TripleBandLinearOp
from qtmodel.methods.finitedifferences.utilities.fdmquantohelper import FdmQuantoHelper
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.types import Real


class FdmBlackScholesOp(FdmLinearOpComposite):

    def __init__(self,
                 mesher: FdmMesher,
                 bs_process: GeneralizedBlackScholesProcess,
                 strike: Real,
                 local_vol: bool = False,
                 illegal_local_vol_overwrite: Real = None,
                 direction: int = 0,
                 quanto_helper: FdmQuantoHelper = None):
        self._mesher = mesher
        self._r_ts = bs_process.risk_free_rate().current_link()
        self._q_ts = bs_process.dividend_yield().current_link()
        self._vol_ts = bs_process.black_volatility().current_link()
        self._local_vol = bs_process.local_volatility().current_link() if local_vol else None
        self._x = [math.exp(i) for i in mesher.locations(direction)] if local_vol else []
        self._dx_map = FirstDerivativeOp(direction, mesher)
        self._dxx_map = SecondDerivativeOp(direction, mesher)
        self._map_t = TripleBandLinearOp(direction, mesher)
        self._strike = strike
        self._illegal_local_vol_overwrite = illegal_local_vol_overwrite
        self._direction = direction
        self._quanto_helper = quanto_helper

    def size(self):
        return 1

    def set_time(self,
                 t1: Real,
                 t2: Real):
        r = self._r_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()
        q = self._q_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()

        if self._local_vol is not None:
            layout = self._mesher.layout()
            end_iter = layout.end()

            v = [None] * layout.size()
            iter = layout.begin()
            while iter != end_iter:
                i = iter.index()

                if self._illegal_local_vol_overwrite < 0.0:
                    v[i] = math.pow(self._local_vol.local_vol(t=0.5 * (t1 + t2),
                                                              underlying_level=self._x[i],
                                                              extrapolate=True), 2)
                else:
                    try:
                        v[i] = math.pow(self._local_vol.local_vol(t=0.5 * (t1 + t2),
                                                                  underlying_level=self._x[i],
                                                                  extrapolate=True), 2)
                    except:
                        v[i] = math.pow(self._illegal_local_vol_overwrite, 2)
                iter.increment()

            if self._quanto_helper is not None and self._quanto_helper._r_ts is not None:
                _tmp = [r - q - 0.5 * i for i in v]
                self._map_t.axpyb([m - n for m, n in
                                   zip(_tmp, self._quanto_helper.quanto_adjustment([math.sqrt(i) for i in v], t1, t2))],
                                  self._dx_map, self._dxx_map.mult([0.5 * i for i in v]), [-r])
            else:
                _tmp = [r - q - 0.5 * i for i in v]
                self._map_t.axpyb(_tmp, self._dx_map,
                                  self._dxx_map.mult([0.5 * i for i in v]), [-r])
        else:
            v = self._vol_ts.black_forward_variance(t1, t2, self._strike) / (t2 - t1)

            if self._quanto_helper is not None and self._quanto_helper._r_ts is not None:
                _tmp = [r - q - 0.5 * v]
                _tmp2 = [v] * self._mesher.layout().size()
                self._map_t.axpyb([m - n for m, n in zip(_tmp, self._quanto_helper.quanto_adjustment(
                    [math.sqrt(v)], t1, t2))],
                                  self._dx_map,
                                  self._dxx_map.mult([0.5 * i for i in _tmp2]),
                                  [-r])
            else:
                _tmp = [v] * self._mesher.layout().size()
                self._map_t.axpyb([r - q - 0.5 * v], self._dx_map,
                                  self._dxx_map.mult([0.5 * i for i in _tmp]), [-r])

    def apply(self, r: list):
        return self._map_t.apply(r)

    def apply_mixed(self, r: list):
        return [0.0] * len(r)

    def apply_direction(self, direction: int, r: list):
        if direction == self._direction:
            return self._map_t.apply(r)
        else:
            return [0.0] * len(r)

    def solve_splitting(self, direction: int, r: list, dt: Real):
        if direction == self._direction:
            return self._map_t.solve_splitting(r, dt, 1.0)
        else:
            return r

    def preconditioner(self, r: list, dt: Real):
        return self.solve_splitting(self._direction, r, dt)

    def to_matrix_decomp(self):
        return [self._map_t.to_matrix()]