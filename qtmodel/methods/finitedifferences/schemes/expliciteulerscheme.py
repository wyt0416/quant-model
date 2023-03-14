from typing import List

from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.types import Real


class ExplicitEulerScheme:

    def __init__(self, map: FdmLinearOpComposite, bc_set: List[BoundaryCondition]):
        self._dt: Real = None
        self._map = map
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)

    def step(self, a: list, t: Real, theta: Real = None):
        if theta is None:
            self.step(a, t, 1.0)
        else:
            qt_require(t - self._dt > -1e-8, "a step towards negative time given")
            self._map.set_time(max(0.0, t - self._dt), t)
            self._bc_set.set_time(max(0.0, t - self._dt))

            self._bc_set.apply_before_applying(self._map)
            _tmp = [i + (theta * self._dt) * j for i, j in zip(a, self._map.apply(a))]
            a.clear()
            a.extend(_tmp)
            self._bc_set.apply_after_applying(a)

    def set_step(self, dt: Real):
        self._dt = dt
