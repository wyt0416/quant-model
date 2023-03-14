import copy
from enum import Enum
from typing import List

from qtmodel.error import qt_require, QTError
from qtmodel.math.matrixutilities.bicgstab import BiCGstab
from qtmodel.math.matrixutilities.gmres import GMRES
from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.boundaryconditionschemehelper import BoundaryConditionSchemeHelper
from qtmodel.methods.finitedifferences.schemes.impliciteulerscheme import ImplicitEulerSchemeSolverType
from qtmodel.types import Real


class TrBDF2SchemeSolverTypes(Enum):
    BiCGstab = "BiCGstab"
    GMRES = "GMRES"


class TrBDF2Scheme:

    def __init__(self,
                 alpha: Real,
                 map: FdmLinearOpComposite,
                 trapezoidal_scheme,
                 bc_set: List[BoundaryCondition],
                 rel_tol: Real = -1e-8,
                 solver_type: TrBDF2SchemeSolverTypes = TrBDF2SchemeSolverTypes.BiCGstab):
        self._dt = None
        self._beta = None
        self._iterations = None
        self._alpha = alpha
        self._map = map
        self._trapezoidal_scheme = trapezoidal_scheme
        self._bc_set = BoundaryConditionSchemeHelper(bc_set)
        self._rel_tol = rel_tol
        self._solver_type = solver_type

    def set_step(self, dt: Real):
        self._dt = dt
        self._beta = (1.0 - self._alpha) / (2.0 - self._alpha) * self._dt

    def number_of_iterations(self):
        return self._iterations

    def apply(self, r: list):
        return [i - self._beta * j for i, j in zip(r, self._map.apply(r))]

    def step(self, fn: list, t: Real):
        qt_require(t - self._dt > -1e-8, "a step towards negative time given")

        intermediate_time_step = self._dt * self._alpha

        f_star = copy.deepcopy(fn)
        self._trapezoidal_scheme.set_step(intermediate_time_step)
        self._trapezoidal_scheme.step(f_star, t)

        self._bc_set.set_time(max(0.0, t - self._dt))
        self._bc_set.apply_before_solving(self._map, fn)

        f = [(1 / self._alpha * i - pow((1 - self._alpha), 2) / self._alpha * j) / (2 - self._alpha) for i, j in zip(f_star, fn)]

        if self._map.size() == 1:
            fn.clear()
            fn.extend(self._map.solve_splitting(0, f, -self._beta))
        else:
            preconditioner = lambda _a: self._map.preconditioner(_a, -self._beta)
            apply_f = lambda _a: self.apply(_a)

            if self._solver_type == TrBDF2SchemeSolverTypes.BiCGstab:
                result = BiCGstab(apply_f, max(10, len(fn)), self._rel_tol, preconditioner).solve(
                    f, f)

                self._iterations += result.iterations
                fn.clear()
                fn.extend(result.x)
            elif self._solver_type == TrBDF2SchemeSolverTypes.GMRES:
                result = GMRES(apply_f, max(10, int(len(fn) / 10)), self._rel_tol,
                                        preconditioner).solve(f, f)

                self._iterations += len(result.errors)
                fn.clear()
                fn.extend(result.x)
            else:
                QTError("unknown/illegal solver type")

        self._bc_set.apply_after_solving(fn)
