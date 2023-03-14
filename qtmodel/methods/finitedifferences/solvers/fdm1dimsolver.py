import copy

from qtmodel.math.interpolations.cubicinterpolation import CubicInterpolation, MonotonicCubicNaturalSpline
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.solvers.fdmbackwardsolver import FdmSchemeDesc, FdmBackwardSolver
from qtmodel.methods.finitedifferences.solvers.fdmsolverdesc import FdmSolverDesc
from qtmodel.methods.finitedifferences.stepconditions.fdmsnapshotcondition import FdmSnapshotCondition
from qtmodel.methods.finitedifferences.stepconditions.fdmstepconditioncomposite import FdmStepConditionComposite
from qtmodel.patterns.lazyobject import LazyObject
from qtmodel.types import Real


class Fdm1DimSolver(LazyObject):

    def __init__(self,
                 solver_desc: FdmSolverDesc,
                 scheme_desc: FdmSchemeDesc,
                 op: FdmLinearOpComposite):
        super(Fdm1DimSolver, self).__init__()
        self._solver_desc = solver_desc
        self._scheme_desc = scheme_desc
        self._op = op
        self._theta_condition = FdmSnapshotCondition(0.99 * min(1.0 / 365.0, solver_desc.maturity if len(solver_desc.condition.stopping_times()) == 0 else solver_desc.condition.stopping_times()[0]))
        self._conditions = FdmStepConditionComposite.join_conditions(self._theta_condition, solver_desc.condition)
        self._x = [None] * solver_desc.mesher.layout().size()
        self._initial_values = [None] * solver_desc.mesher.layout().size()
        self._result_values = [None] * solver_desc.mesher.layout().size()
        self._interpolation: CubicInterpolation = None

        mesher = solver_desc.mesher
        layout = mesher.layout()

        end_iter = layout.end()
        iter = layout.begin()
        while iter != end_iter:
            self._initial_values[iter.index()] = self._solver_desc.calculator.avg_inner_value(iter, solver_desc.maturity)
            self._x[iter.index()] = mesher.location(iter, 0)
            iter.increment()

    def interpolate_at(self, x: Real):
        self.calculate()
        return self._interpolation(x)

    def theta_at(self, x: Real):
        if self._conditions.stopping_times()[0] == 0.0:
            return None

        self.calculate()

        rhs = self._theta_condition.get_values()
        theta_values = copy.deepcopy(rhs)

        temp = MonotonicCubicNaturalSpline(self._x, theta_values)(x)
        return (temp - self.interpolate_at(x)) / self._theta_condition.get_time()

    def derivative_x(self, x: Real):
        self.calculate()
        return self._interpolation.derivative(x)

    def derivative_x_x(self, x: Real):
        self.calculate()
        return self._interpolation.second_derivative(x)

    def perform_calculations(self):
        rhs = copy.deepcopy(self._initial_values)
        FdmBackwardSolver(self._op, self._solver_desc.bc_set, self._conditions, self._scheme_desc).rollback(rhs, self._solver_desc.maturity, 0.0,
                  self._solver_desc.time_steps, self._solver_desc.damping_steps)

        self._result_values = copy.deepcopy(rhs)
        self._interpolation = MonotonicCubicNaturalSpline(self._x, self._result_values)
