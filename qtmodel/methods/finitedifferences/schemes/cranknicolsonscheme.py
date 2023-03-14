from typing import List

from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.expliciteulerscheme import ExplicitEulerScheme
from qtmodel.methods.finitedifferences.schemes.impliciteulerscheme import ImplicitEulerSchemeSolverType, \
    ImplicitEulerScheme
from qtmodel.types import Real


class CrankNicolsonScheme:
    """
    In one dimension the Crank-Nicolson scheme is equivalent to the
    Douglas scheme and in higher dimensions it is usually inferior to
    operator splitting methods like Craig-Sneyd or Hundsdorfer-Verwer.
    """

    def __init__(self,
                 theta: Real,
                 map: FdmLinearOpComposite,
                 bc_set: List[BoundaryCondition],
                 rel_tol: Real = 1e-8,
                 solver_type: ImplicitEulerSchemeSolverType = ImplicitEulerSchemeSolverType.BiCGstab):
        self._dt = None
        self._theta = theta
        self._explicit = ExplicitEulerScheme(map, bc_set)
        self._implicit = ImplicitEulerScheme(map, bc_set, rel_tol, solver_type)

    def step(self, a: list, t: Real):
        qt_require(t - self._dt > -1e-8, "a step towards negative time given")

        if self._theta != 1.0:
            self._explicit.step(a, t, 1.0 - self._theta)

        if self._theta != 0.0:
            self._implicit.step(a, t, self._theta)

    def set_step(self, dt: Real):
        self._dt = dt
        self._explicit.set_step(self._dt)
        self._implicit.set_step(self._dt)

    def number_of_iterations(self):
        return self._implicit.number_of_iterations()
