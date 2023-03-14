from typing import List

from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.types import Real


class DouglasScheme:

    def __init__(self,
                 theta: Real,
                 map: FdmLinearOpComposite,
                 bc_set: List[BoundaryCondition]):
        self._dt = None
        self._theta = theta
        self._map = map
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)

    def step(self, a: list, t: Real):
        qt_require(t - self._dt > -1e-8, "a step towards negative time given")
        self._map.set_time(max(0.0, t - self._dt), t)
        self._bc_set.set_time(max(0.0, t - self._dt))

        self._bc_set.apply_before_applying(self._map)
        y = [m + self._dt * n for m, n in zip(a, self._map.apply(a))]
        self._bc_set.apply_after_applying(y)

        for i in range(self._map.size()):
            rhs = [m - self._theta * self._dt * n for m, n in zip(y, self._map.apply_direction(i, a))]
            y = self._map.solve_splitting(i, rhs, -self._theta * self._dt)

        self._bc_set.apply_after_solving(y)

        a.clear()
        a.extend(y)

    def set_step(self, dt: Real):
        self._dt = dt
