import math
import sys
from typing import List, Optional

from qtmodel.error import qt_require
from qtmodel.math.abcdmathfunction import AbcdMathFunction
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution
from qtmodel.math.optimization.constraint import NoConstraint
from qtmodel.math.optimization.costfunction import CostFunction, ParametersTransformation
from qtmodel.math.optimization.endcriteria import EndCriteria, EndCriteriaTypes
from qtmodel.math.optimization.levenbergmarquardt import LevenbergMarquardt
from qtmodel.math.optimization.method import OptimizationMethod
from qtmodel.math.optimization.problem import Problem
from qtmodel.math.optimization.projectedcostfunction import ProjectedCostFunction
from qtmodel.termstructures.volatility.abcd import abcd_black_volatility
from qtmodel.types import Real


class AbcdCalibration:
    def __init__(self,
                 t: list,
                 black_vols: list,
                 a: Real = -0.06,
                 b: Real = 0.17,
                 c: Real = 0.54,
                 d: Real = 0.17,
                 a_is_fixed: bool = False,
                 b_is_fixed: bool = False,
                 c_is_fixed: bool = False,
                 d_is_fixed: bool = False,
                 vega_weighted: bool = False,
                 end_criteria: EndCriteria = None,
                 opt_method: OptimizationMethod = None):
        self._a_is_fixed = a_is_fixed
        self._b_is_fixed = b_is_fixed
        self._c_is_fixed = c_is_fixed
        self._d_is_fixed = d_is_fixed
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._abcd_end_criteria = EndCriteriaTypes.Null
        self._end_criteria = end_criteria
        self._opt_method = opt_method
        _black_vols_len = len(black_vols)
        self._weights = [1.0 / _black_vols_len] * _black_vols_len
        self._vega_weighted = vega_weighted
        self._times = t
        self._black_vols = black_vols
        self._transformation = None

        AbcdMathFunction.validate(a, b, c, d)

        qt_require(len(black_vols) == len(t),
                   f"mismatch between number of times ({len(t)}) and black_vols ({len(black_vols)})")

        # if no optimization method or endCriteria is provided, we provide one
        if not self._opt_method:
            epsfcn = 1.0e-8
            xtol = 1.0e-8
            gtol = 1.0e-8
            use_cost_functions_jacobian = False
            self._opt_method = LevenbergMarquardt(epsfcn, xtol, gtol, use_cost_functions_jacobian)
        if not self._end_criteria:
            max_iterations = 10000
            max_stationary_state_iterations = 1000
            root_epsilon = 1.0e-8
            function_epsilon = 0.3e-4  # Why 0.3e-4 ?
            gradient_norm_epsilon = 0.3e-4  # Why 0.3e-4 ?
            self._end_criteria = EndCriteria(max_iterations,
                                             max_stationary_state_iterations,
                                             root_epsilon,
                                             function_epsilon,
                                             gradient_norm_epsilon)

    def k(self, t: list, black_vols: list):
        _t_len = len(t)
        _black_vols_len = len(black_vols)
        qt_require(_black_vols_len == _t_len,
                   f"mismatch between number of times ({_t_len}) and black_vols ({_black_vols_len})")
        k = [None] * _t_len
        for i in range(_t_len):
            k[i] = black_vols[i] / self.value(t[i])

        return k

    def compute(self):
        if self._vega_weighted:
            weights_sum = 0.0
            _times_len = len(self._times)
            for i in range(_times_len):
                std_dev = math.sqrt(self._black_vols[i] * self._black_vols[i] * self._times[i])
                # when strike==forward, the blackFormulaStdDevDerivative becomes
                self._weights[i] = CumulativeNormalDistribution().derivative(.5 * std_dev)
                weights_sum += self._weights[i]
            # weight normalization
            for i in range(_times_len):
                self._weights[i] /= weights_sum

        # there is nothing to optimize
        if self._a_is_fixed and self._b_is_fixed and self._c_is_fixed and self._d_is_fixed:
            self._abcd_end_criteria = EndCriteriaTypes.Null
            # error_ = interpolationError()
            # maxError_ = interpolationMaxError()
            return
        else:
            cost_function = AbcdError(self)
            self._transformation = AbcdParametersTransformation()

            guess: List[Optional[Real]] = [None] * 4
            guess[0] = self._a
            guess[1] = self._b
            guess[2] = self._c
            guess[3] = self._d

            parameter_are_fixed: List[Optional[bool]] = [None] * 4
            parameter_are_fixed[0] = self._a_is_fixed
            parameter_are_fixed[1] = self._b_is_fixed
            parameter_are_fixed[2] = self._c_is_fixed
            parameter_are_fixed[3] = self._d_is_fixed

            inversed_transformated_guess = self._transformation.inverse(guess)

            projected_abcd_cost_function = ProjectedCostFunction(cost_function, inversed_transformated_guess,
                                                                 parameter_are_fixed)

            projected_guess = projected_abcd_cost_function.project(inversed_transformated_guess)

            constraint = NoConstraint()
            problem = Problem(projected_abcd_cost_function, constraint, projected_guess)
            self._abcd_end_criteria = self._opt_method.minimize(problem, self._end_criteria)
            projected_result = problem.current_value()
            transf_result = projected_abcd_cost_function.include(projected_result)

            result = self._transformation.direct(transf_result)
            AbcdMathFunction.validate(self._a, self._b, self._c, self._d)
            self._a = result[0]
            self._b = result[1]
            self._c = result[2]
            self._d = result[3]

    def value(self, x: Real):
        return abcd_black_volatility(x, self._a, self._b, self._c, self._d)

    def error(self):
        _times_len = len(self._times)
        n = _times_len
        squared_error = 0.0
        for i in range(_times_len):
            error = (self.value(self._times[i]) - self._black_vols[i])
            squared_error += error * error * self._weights[i]
        return math.sqrt(n * squared_error / (n - 1))

    def max_error(self):
        max_error = sys.float_info.max
        for i in range(len(self._times)):
            error = abs(self.value(self._times[i]) - self._black_vols[i])
            max_error = max(max_error, error)
        return max_error

    def errors(self):
        """ calculate weighted differences """
        _times_len = len(self._times)
        results = [None] * _times_len
        for i in range(_times_len):
            results[i] = (self.value(self._times[i]) - self._black_vols[i]) * math.sqrt(self._weights[i])
        return results

    def end_criteria(self):
        return self._abcd_end_criteria

    def a(self):
        return self._a

    def b(self):
        return self._b

    def c(self):
        return self._c

    def d(self):
        return self._d


class AbcdError(CostFunction):

    def __init__(self, abcd: AbcdCalibration):
        self._abcd = abcd

    def value(self, x: list):
        y = self._abcd._transformation.direct(x)
        self._abcd._a = y[0]
        self._abcd._b = y[1]
        self._abcd._c = y[2]
        self._abcd._d = y[3]
        return self._abcd.error()

    def values(self, x: list):
        y = self._abcd._transformation.direct(x)
        self._abcd._a = y[0]
        self._abcd._b = y[1]
        self._abcd._c = y[2]
        self._abcd._d = y[3]
        return self._abcd.errors()


class AbcdParametersTransformation(ParametersTransformation):

    def __init__(self):
        self._y: List[Optional[Real]] = [None] * 4

    def direct(self, x: list):
        """ to constrained <- from unconstrained """
        self._y[1] = x[1]
        self._y[2] = math.exp(x[2])
        self._y[3] = math.exp(x[3])
        self._y[0] = math.exp(x[0]) - self._y[3]
        return self._y

    def inverse(self, x: list):
        """ to unconstrained <- from constrained """
        self._y[1] = x[1]
        self._y[2] = math.log(x[2])
        self._y[3] = math.log(x[3])
        self._y[0] = math.log(x[0] + x[3])
        return self._y
