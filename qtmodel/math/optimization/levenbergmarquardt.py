import copy

import numpy as np

from qtmodel.error import qt_require
from qtmodel.math.optimization.endcriteria import EndCriteria, EndCriteriaTypes
from qtmodel.math.optimization.lmdif import MINPACK
from qtmodel.math.optimization.method import OptimizationMethod
from qtmodel.math.optimization.problem import Problem
from qtmodel.types import Real


class LevenbergMarquardt(OptimizationMethod):
    """
    Levenberg-Marquardt optimization method
    This implementation is based on MINPACK
    (<http://www.netlib.org/minpack>,
    <http://www.netlib.org/cephes/linalg.tgz>)
    It has a built in fd scheme to compute
    the jacobian, which is used by default.
    If useCostFunctionsJacobian is true the
    corresponding method in the cost function
    of the problem is used instead. Note that
    the default implementation of the jacobian
    in CostFunction uses a central difference
    (oder 2, but requiring more function
    evaluations) compared to the forward
    difference implemented here (order 1).
    """

    def __init__(self,
                 epsfcn: Real = 1.0e-8,
                 xtol: Real = 1.0e-8,
                 gtol: Real = 1.0e-8,
                 use_cost_functions_jacobian: bool = False):
        self._epsfcn = epsfcn
        self._xtol = xtol
        self._gtol = gtol
        self._use_cost_functions_jacobian = use_cost_functions_jacobian
        self._current_problem: Problem = None
        self._init_cost_values: list = None
        self._init_jacobian: np.ndarray = None
        self._info: int = 0

    def get_info(self):
        return self._info

    def minimize(self, p: Problem, end_criteria: EndCriteria):
        ec_type = EndCriteriaTypes.Null
        p.reset()
        x_ = p.current_value()
        self._current_problem = p
        self._init_cost_values = p.cost_function().values(x_)
        m = self._init_cost_values.size()
        n = len(x_)
        if self._use_cost_functions_jacobian:
            self._init_jacobian = np.zeros((m, n))
            p.cost_function().jacobian(self._init_jacobian, x_)
        xx = copy.deepcopy(x_)
        fvec = [None] * m
        diag = [None] * n
        mode = 1
        factor = 1
        nprint = 0
        info = 0
        nfev = 0
        fjac = [None] * (m * n)
        ldfjac = m
        ipvt = [None] * n
        qtf = [None] * n
        wa1 = [None] * n
        wa2 = [None] * n
        wa3 = [None] * n
        wa4 = [None] * m
        # requirements; check here to get more detailed error messages.
        qt_require(n > 0, "no variables given")
        qt_require(m >= n, f"less functions ({m}) than available variables ({n})")
        qt_require(end_criteria.function_epsilon() >= 0.0, "negative f tolerance")
        qt_require(self._xtol >= 0.0, "negative x tolerance")
        qt_require(self._gtol >= 0.0, "negative g tolerance")
        qt_require(end_criteria.max_iterations() > 0, "null number of evaluations")

        # call lmdif to minimize the sum of the squares of m functions
        # in n variables by the Levenberg-Marquardt algorithm.
        info, nfev = MINPACK.lmdif(m, n, xx, fvec,
                                   end_criteria.function_epsilon(),
                                   self._xtol,
                                   self._gtol,
                                   end_criteria.max_iterations(),
                                   self._epsfcn,
                                   diag, mode, factor,
                                   nprint, info, nfev, fjac,
                                   ldfjac, ipvt, qtf,
                                   wa1, wa2, wa3, wa4,
                                   self.fcn,
                                   self.jac_fcn)
        self._info = info
        # check requirements & endCriteria evaluation
        qt_require(info != 0, "MINPACK: improper input parameters")
        # qt_require(info != 6, "MINPACK: ftol is too small. no further reduction in the sum of squares is possible.")
        if info != 6:
            ec_type = EndCriteriaTypes.StationaryFunctionValue
        # qt_require(info != 5, "MINPACK: number of calls to fcn has reached or exceeded maxfev.")
        _, ec_type = end_criteria.check_max_iterations(nfev, ec_type)
        qt_require(info != 7,
                   "MINPACK: xtol is too small. no further improvement "
                   "in the approximate solution x is possible.")
        qt_require(info != 8,
                   "MINPACK: gtol is too small. fvec is orthogonal "
                   "to the columns of the jacobian to machine precision.")
        # set problem
        x_ = copy.deepcopy(xx)
        p.set_current_value(x_)
        p.set_function_value(p.cost_function().value(x_))

        return ec_type

    def fcn(self,
            m: int,
            n: int,
            x: list,
            fvec: list,
            iflag: int):
        xt = copy.deepcopy(x)
        # constraint handling needs some improvement in the future:
        # starting point should not be close to a constraint violation
        if self._current_problem.constraint().test(xt):
            tmp = self._current_problem.values(xt)
            fvec.clear()
            fvec.extend(tmp)
        else:
            fvec.clear()
            fvec.extend(self._init_cost_values)

    def jac_fcn(self,
                m: int,
                n: int,
                x: list,
                fjac: list,
                iflag: int):
        xt = copy.deepcopy(x)
        # constraint handling needs some improvement in the future:
        # starting point should not be close to a constraint violation
        if self._current_problem.constraint().test(xt):
            tmp = np.zeros((m, n))
            self._current_problem.cost_function().jacobian(tmp, xt)
            tmp_t = tmp.transpose()
            fjac.clear()
            fjac.extend(tmp_t)
        else:
            tmp_t = self._init_jacobian.transpose()
            fjac.clear()
            fjac.extend(tmp_t)
