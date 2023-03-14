import sys
from enum import Enum

from qtmodel.error import qt_require
from qtmodel.types import Real


class EndCriteriaTypes(Enum):
    Null = "null"
    MaxIterations = "max iterations"
    StationaryPoint = "stationary point"
    StationaryFunctionValue = "stationary function value"
    StationaryFunctionAccuracy = "stationary function accuracy"
    ZeroGradientNorm = "zero gradient norm"
    Unknown = "unknown"


class EndCriteria:
    """
    Criteria to end optimization process:
    - maximum number of iterations AND minimum number of iterations around stationary point
    - x (independent variable) stationary point
    - y=f(x) (dependent variable) stationary point
    - stationary gradient
    """

    def __init__(self,
                 max_iterations: int,
                 max_stationary_state_iterations: int,
                 root_epsilon: Real,
                 function_epsilon: Real,
                 gradient_norm_epsilon: Real):
        self._max_iterations = max_iterations
        self._max_stationary_state_iterations = max_stationary_state_iterations
        self._root_epsilon = root_epsilon
        self._function_epsilon = function_epsilon
        self._gradient_norm_epsilon = gradient_norm_epsilon
        if self._max_stationary_state_iterations == sys.maxsize:
            self._max_stationary_state_iterations = min(int(max_iterations / 2), 100)
        qt_require(self._max_stationary_state_iterations > 1,
                   f"max_stationary_state_iterations ({self._max_stationary_state_iterations}) must be greater than one")
        qt_require(self._max_stationary_state_iterations < self._max_iterations,
                   f"max_stationary_state_iterations ({self._max_stationary_state_iterations}) must be less than maxIterations_ ({self._max_iterations})")
        if self._gradient_norm_epsilon == sys.float_info.max:
            self._gradient_norm_epsilon_ = self._function_epsilon

    def max_iterations(self):
        return self._max_iterations

    def max_stationary_state_iterations(self):
        return self._max_stationary_state_iterations

    def root_epsilon(self):
        return self._root_epsilon

    def function_epsilon(self):
        return self._function_epsilon

    def gradient_norm_epsilon(self):
        return self._gradient_norm_epsilon

    def __call__(self,
                 iteration: int,
                 stat_state_iterations: int,
                 positive_optimization: bool,
                 fold: Real,
                 normgold: Real,
                 fnew: Real,
                 normgnew: Real,
                 ec_type: EndCriteriaTypes):
        """
        Test if the number of iterations is not too big and if a minimum point is not reached
        :param iteration:
        :param stat_state_iterations:
        :param positive_optimization:
        :param fold:
        :param normgold:
        :param fnew:
        :param normgnew:
        :param ec_type:
        :return:
        """
        return self.check_max_iterations(iteration, ec_type)[0] or \
               self.check_stationary_function_value(fold, fnew, stat_state_iterations, ec_type)[0] or \
               self.check_stationary_function_accuracy(fnew, positive_optimization, ec_type)[0] or \
               self.check_zero_gradient_norm(normgnew, ec_type)[0]

    def check_max_iterations(self, iteration: int, ec_type: EndCriteriaTypes):
        """
        Test if the number of iteration is below max_iterations
        :param iteration:
        :param ec_type:
        :return:
        """
        if iteration < self._max_iterations:
            return False, ec_type
        ec_type = EndCriteriaTypes.MaxIterations
        return True, ec_type

    def check_stationary_point(self,
                               x_old: Real,
                               x_new: Real,
                               stat_state_iterations: int,
                               ec_type: EndCriteriaTypes):
        """
        Test if the root variation is below rootEpsilon
        :param x_old:
        :param x_new:
        :param stat_state_iterations:
        :param ec_type:
        :return:
        """
        if abs(x_new - x_old) >= self._root_epsilon:
            stat_state_iterations = 0
            return False, stat_state_iterations, ec_type

        stat_state_iterations += 1
        if stat_state_iterations <= self._max_stationary_state_iterations:
            return False, stat_state_iterations, ec_type
        ec_type = EndCriteriaTypes.StationaryPoint
        return True, stat_state_iterations, ec_type

    def check_stationary_function_value(self,
                                        fx_old: Real,
                                        fx_new: Real,
                                        stat_state_iterations: int,
                                        ec_type: EndCriteriaTypes):
        """
        Test if the function variation is below functionEpsilon
        :param fx_old:
        :param fx_new:
        :param stat_state_iterations:
        :param ec_type:
        :return:
        """
        if abs(fx_new - fx_old) >= self._function_epsilon:
            stat_state_iterations = 0
            return False, stat_state_iterations, ec_type

        stat_state_iterations += 1
        if stat_state_iterations <= self._max_stationary_state_iterations:
            return False, stat_state_iterations, ec_type
        ec_type = EndCriteriaTypes.StationaryFunctionValue
        return True, stat_state_iterations, ec_type

    def check_stationary_function_accuracy(self,
                                           f: Real,
                                           positive_optimization: bool,
                                           ec_type: EndCriteriaTypes):
        """
        Test if the function value is below functionEpsilon
        :param f:
        :param positive_optimization:
        :param ec_type:
        :return:
        """
        if not positive_optimization:
            return False, ec_type
        if f >= self._function_epsilon:
            return False, ec_type
        ec_type = EndCriteriaTypes.StationaryFunctionAccuracy
        return True, ec_type

    def check_zero_gradient_norm(self,
                                 gradient_norm: Real,
                                 ec_type: EndCriteriaTypes):
        """
        Test if the gradient norm value is below gradientNormEpsilon
        :param gradient_norm:
        :param ec_type:
        :return:
        """
        if gradient_norm >= self._gradient_norm_epsilon:
            return False, ec_type
        ec_type = EndCriteriaTypes.ZeroGradientNorm
        return True, ec_type
