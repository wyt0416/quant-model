from typing import List

from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.types import Real


class ModifiedCraigSneydScheme(object):
    """
    modified Craig-Sneyd scheme

    References:
       K. J. in 't Hout and S. Foulon,
       ADI finite difference schemes for option pricing in the Heston
       model with correlation, http://arxiv.org/pdf/0811.3427
    """

    def __init__(self, theta: Real, mu: Real, map: FdmLinearOpComposite, bc_set: List[BoundaryCondition]):
        self._dt = None
        self._theta = theta
        self._mu = mu
        self._map = map
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)

    def step(self, a: list, t: Real):
        qt_require(t - self._dt > -1e-8, "a step towards negative time given")

        self._map.set_time(max(0.0, t - self._dt), t)
        self._bc_set.set_time(max(0.0, t - self._dt))

        self._bc_set.apply_before_applying(self._map)
        y = [i + self._dt*j for i, j in zip(a, self._map.apply(a))]
        self._bc_set.apply_after_applying(y)

        y0 = y

        i = 0
        while i < self._map.size():
            rhs = y - self._theta * self._dt * self._map.apply_direction(i, a)
            y = self._map.solve_splitting(i, rhs, -self._theta * self._dt)
            i += 1

        self._bc_set.apply_before_applying(self._map)

        _tmp = [i-j for i, j in zip(y, a)]
        yt = [i + self._mu * self._dt * j + (0.5 - self._mu) * self._dt * z
              for i, j, z in zip(y0, self._map.apply_mixed(_tmp), self._map.apply(_tmp))]
        self._bc_set.apply_after_applying(yt)

        i = 0
        while i < self._map.size():
            rhs = [i - self._theta * self._dt * j for i, j in zip(yt, self._map.apply_direction(i, a))]
            yt = self._map.solve_splitting(i, rhs, -self._theta * self._dt)
            i += 1
        self._bc_set.apply_after_solving(yt)

        a.clear()
        a.extend(yt)

    def set_step(self, dt: Real):
        self._dt = dt
