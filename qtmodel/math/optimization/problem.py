import sys
from typing import Optional

from qtmodel.error import qt_require
from qtmodel.math.optimization.constraint import Constraint
from qtmodel.math.optimization.costfunction import CostFunction
from qtmodel.types import Real


class Problem:
    """ Constrained optimization problem """

    def __init__(self,
                 cost_function: CostFunction,
                 constraint: Constraint,
                 initial_value: list):
        qt_require(not constraint.empty(), "empty constraint given")
        self._cost_function = cost_function  # Unconstrained cost function
        self._constraint = constraint  # Constraint
        self._current_value = initial_value  # current value of the local minimum
        # function and gradient norm values at the currentValue_ (i.e. the last step)
        self._function_value: Optional[Real] = None
        self._squared_norm: Optional[Real] = None
        # number of evaluation of cost function and its gradient
        self._function_evaluation: Optional[int] = None
        self._gradient_evaluation: Optional[int] = None

    def reset(self):
        """ it does not reset the current minumum to any initial value """
        self._function_evaluation = self._gradient_evaluation = 0
        self._function_value = self._squared_norm = sys.float_info.max

    def value(self, x: list):
        """ call cost function computation and increment evaluation counter """
        self._function_evaluation += 1
        return self._cost_function.value(x)

    def values(self, x: list):
        """ call cost values computation and increment evaluation counter """
        self._function_evaluation += 1
        return self._cost_function.values(x)

    def gradient(self, grad_f: list, x: list):
        """ call cost function gradient computation and increment evaluation counter """
        self._gradient_evaluation += 1
        self._cost_function.gradient(grad_f, x)

    def value_and_gradient(self, grad_f: list, x: list):
        """ call cost function computation and it gradient """
        self._function_evaluation += 1
        self._gradient_evaluation += 1
        return self._cost_function.value_and_gradient(grad_f, x)

    def constraint(self):
        """ Constraint """
        return self._constraint

    def cost_function(self):
        """ Cost function """
        return self._cost_function

    def set_current_value(self, current_value: list):
        self._current_value = current_value

    def current_value(self):
        return self._current_value

    def set_function_value(self, function_value: Real):
        self._function_value = function_value

    def function_value(self):
        """ value of cost function """
        return self._function_value

    def set_gradient_norm_value(self, squared_norm: Real):
        self._squared_norm = squared_norm

    def gradient_norm_value(self):
        """ value of cost function gradient norm """
        return self._squared_norm

    def function_evaluation(self):
        """ number of evaluation of cost function """
        return self._function_evaluation

    def gradient_evaluation(self):
        """ number of evaluation of cost function gradient """
        return self._gradient_evaluation
