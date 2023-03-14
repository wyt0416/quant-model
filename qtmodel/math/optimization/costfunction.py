import math
from abc import ABCMeta, abstractmethod

import numpy as np


class CostFunction(metaclass=ABCMeta):
    """ Cost function abstract class for optimization problem """

    @staticmethod
    def value(x: list):
        """ method to overload to compute the cost function value in x """
        v = list(x)
        v = list(map(lambda i: i ** 2, v))
        return math.sqrt(np.mean(v))

    @staticmethod
    @abstractmethod
    def values(x: list) -> list:
        """ method to overload to compute the cost function values in x """
        pass

    @staticmethod
    def gradient(grad: list, x: list):
        """
        method to overload to compute grad_f, the first derivative of
        the cost function with respect to x
        :param grad:
        :param x:
        :return:
        """
        eps = CostFunction.finite_difference_epsilon()
        xx = list(x)
        _x_len = len(x)
        for i in range(_x_len):
            xx[i] += eps
            fp = CostFunction.value(xx)
            xx[i] -= 2.0 * eps
            fm = CostFunction.value(xx)
            grad[i] = 0.5 * (fp - fm) / eps
            xx[i] = x[i]

    @staticmethod
    def finite_difference_epsilon():
        """ Default epsilon for finite difference method """
        return 1e-8

    @staticmethod
    def value_and_gradient(grad: list, x: list):
        """
        method to overload to compute grad_f, the first derivative of
        the cost function with respect to x and also the cost function
        :param grad:
        :param x:
        :return:
        """
        CostFunction.gradient(grad, x)
        return CostFunction.value(x)

    @staticmethod
    def jacobian(jac: np.ndarray, x: list):
        """
        method to overload to compute J_f, the jacobian of
        the cost function with respect to x
        :param jac:
        :param x:
        :return:
        """
        eps = CostFunction.finite_difference_epsilon()
        xx = list(x)
        _x_len = len(x)
        for i in range(_x_len):
            xx[i] += eps
            fp = CostFunction.values(xx)
            xx[i] -= 2.0 * eps
            fm = CostFunction.values(xx)
            _fp_len = len(fp)
            for j in range(_fp_len):
                jac[j, i] = 0.5 * (fp[j] - fm[j]) / eps
            xx[i] = x[i]

    @staticmethod
    def values_and_jacobian(jac: np.ndarray, x: list):
        """
        method to overload to compute J_f, the jacobian of
        the cost function with respect to x and also the cost function
        :param jac:
        :param x:
        :return:
        """
        CostFunction.jacobian(jac, x)
        return CostFunction.values(x)


class ParametersTransformation(metaclass=ABCMeta):

    @abstractmethod
    def direct(self, x: list) -> list:
        pass

    @abstractmethod
    def inverse(self, x: list) -> list:
        pass
