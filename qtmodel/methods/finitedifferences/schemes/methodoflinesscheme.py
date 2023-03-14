import copy
from typing import List

from qtmodel.error import qt_require
from qtmodel.math.ode.adaptiverungekutta import AdaptiveRungeKutta
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.types import Real


class MethodOfLinesScheme:
    def __init__(self,
                 eps: Real,
                 rel_init_step_size: Real,
                 map: FdmLinearOpComposite,
                 bc_set: List[BoundaryCondition]):
        self._dt = None
        self._eps = eps
        self._rel_init_step_size = rel_init_step_size
        self._map = map
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)

    def apply(self, t: Real, u: List[Real]):
        self._map.set_time(t, t + 0.0001)
        self._bc_set.apply_before_applying(self._map)

        dxdt = -self._map.apply(copy.deepcopy(u))

        return dxdt

    def step(self, a: list, t: Real):
        qt_require(t-self._dt > -1e-8, "a step towards negative time given")

        v = AdaptiveRungeKutta(self._eps,
                               self._rel_init_step_size*self._dt)(lambda _t, _u: self.apply(_t, _u),
                                                                  copy.deepcopy(a),
                                                                  t,
                                                                  max(0.0, t-self._dt))

        y = v

        self._bc_set.apply_after_solving(y)

        a.clear()
        a.extend(y)

    def set_step(self, dt: Real):
        self._dt = dt
