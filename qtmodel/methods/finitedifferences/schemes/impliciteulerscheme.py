from enum import Enum
from typing import List

from qtmodel.error import qt_require, QTError
from qtmodel.math.matrixutilities.bicgstab import BiCGstab
from qtmodel.math.matrixutilities.gmres import GMRES
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.types import Real


class ImplicitEulerSchemeSolverType(Enum):
    BiCGstab = "BiCGstab"
    GMRES = "GMRES"


class ImplicitEulerScheme:

    def __init__(self,
                 map: FdmLinearOpComposite,
                 bc_set: List[BoundaryCondition],
                 rel_tol: Real = -1e-8,
                 solver_type: ImplicitEulerSchemeSolverType = ImplicitEulerSchemeSolverType.BiCGstab):
        self._dt = None
        self._iterations = 0
        self._rel_tol = rel_tol
        self._map = map
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)
        self._solver_type = solver_type

    def step(self, a: list, t: Real, theta: Real = None):
        if theta is None:
            self.step(a, t, 1.0)
        else:
            qt_require(t - self._dt > -1e-8, "a step towards negative time given")
            self._map.set_time(max(0.0, t - self._dt), t)
            self._bc_set.set_time(max(0.0, t - self._dt))

            self._bc_set.apply_before_solving(self._map, a)

            if self._map.size() == 1:
                _tmp = self._map.solve_splitting(0, a, -theta * self._dt)
                a.clear()
                a.extend(_tmp)
            else:
                preconditioner = lambda _a: self._map.preconditioner(_a, -theta * self._dt)
                apply_f = lambda _a: self.apply(_a, theta)

                if self._solver_type == ImplicitEulerSchemeSolverType.BiCGstab:
                    result = BiCGstab(apply_f, max(10, len(a)), self._rel_tol, preconditioner).solve(
                        a, a)
                    self._iterations += result.iterations
                    a.clear()
                    a.extend(result.x)
                elif self._solver_type == ImplicitEulerSchemeSolverType.GMRES:
                    result = GMRES(apply_f, max(10, int(len(a) / 10)), self._rel_tol, preconditioner).solve(
                        a, a)

                    self._iterations += len(result.errors)
                    a.clear()
                    a.extend(result.x)
                else:
                    QTError("unknown/illegal solver type")
            self._bc_set.apply_after_solving(a)

    def apply(self, r: list, theta: Real):
        return [i - (theta * self._dt) * j for i, j in zip(r, self._map.apply(r))]

    def set_step(self, dt):
        self._dt = dt

    def number_of_iterations(self):
        return self._iterations
