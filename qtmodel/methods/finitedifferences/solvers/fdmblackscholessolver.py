import math

from qtmodel.handle import Handle
from qtmodel.methods.finitedifferences.operators.fdmblackscholesop import FdmBlackScholesOp
from qtmodel.methods.finitedifferences.solvers.fdm1dimsolver import Fdm1DimSolver
from qtmodel.methods.finitedifferences.solvers.fdmbackwardsolver import FdmSchemeDesc
from qtmodel.methods.finitedifferences.solvers.fdmsolverdesc import FdmSolverDesc
from qtmodel.methods.finitedifferences.utilities.fdmquantohelper import FdmQuantoHelper
from qtmodel.patterns.lazyobject import LazyObject
from qtmodel.patterns.observable import Observable, Observer
from qtmodel.types import Real


class FdmBlackScholesSolver(LazyObject, Observable, Observer):

    def __init__(self,
                 process: Handle,
                 strike: Real,
                 solver_desc: FdmSolverDesc,
                 scheme_desc: FdmSchemeDesc = FdmSchemeDesc.douglas(),
                 local_vol: bool = False,
                 illegal_local_vol_overwrite: Real = None,
                 quanto_helper: Handle = Handle(FdmQuantoHelper())):
        LazyObject.__init__(self)
        Observable.__init__(self)
        Observer.__init__(self)
        self._process = process
        self._strike = strike
        self._solver_desc = solver_desc
        self._scheme_desc = scheme_desc
        self._local_vol = local_vol
        self._illegal_local_vol_overwrite = illegal_local_vol_overwrite
        self._quanto_helper = quanto_helper

        self.register_with(self._process)
        self.register_with(self._quanto_helper)

        self._solver: Fdm1DimSolver = None

    def value_at(self, s: Real):
        self.calculate()
        return self._solver.interpolate_at(math.log(s))

    def delta_at(self, s: Real):
        self.calculate()
        return self._solver.derivative_x(math.log(s)) / s

    def gamma_at(self, s: Real):
        self.calculate()
        return (self._solver.derivative_x_x(math.log(s)) - self._solver.derivative_x(math.log(s))) / (s * s)

    def theta_at(self, s: Real):
        return self._solver.theta_at(math.log(s))

    def perform_calculations(self):
        op = FdmBlackScholesOp(
                self._solver_desc.mesher, self._process.current_link(), self._strike,
                self._local_vol, self._illegal_local_vol_overwrite, 0,
                None if self._quanto_helper.empty() else self._quanto_helper.current_link())

        self._solver = Fdm1DimSolver(self._solver_desc, self._scheme_desc, op)
