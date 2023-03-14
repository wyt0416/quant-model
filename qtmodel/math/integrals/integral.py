import sys
from abc import ABCMeta, abstractmethod
from typing import Callable

from qtmodel.error import qt_require


class Integrator(metaclass=ABCMeta):
    def __init__(self, absolute_accuracy, max_evaluations: int):
        qt_require(absolute_accuracy > sys.float_info.epsilon,
                   f"required tolerance ({absolute_accuracy}) not allowed. It must be > {sys.float_info.epsilon}")
        self._absolute_accuracy = absolute_accuracy
        self._max_evaluations = max_evaluations
        self._absolute_error = None
        self._evaluations = None

    def __call__(self, f: Callable[[float], float], a, b):
        self._evaluations = 0
        if a == b:
            return 0.0
        if b > a:
            return self.integrate(f, a, b)
        else:
            return -self.integrate(f, b, a)

    @abstractmethod
    def integrate(self, f: Callable[[float], float], a, b):
        pass

    def set_absolute_error(self, error):
        self._absolute_error = error

    def set_number_of_evaluations(self, evaluations: int):
        self._evaluations = evaluations

    def increase_number_of_evaluations(self, increase: int):
        self._evaluations += increase

    def set_absolute_accuracy(self, accuracy):
        self._absolute_accuracy = accuracy

    def set_max_evaluations(self, max_evaluations: int):
        self._max_evaluations = max_evaluations

    def absolute_accuracy(self):
        return self._absolute_accuracy

    def max_evaluations(self):
        return self._max_evaluations

    def absolute_error(self):
        return self._absolute_error

    def number_of_evaluations(self):
        return self._evaluations

    def integration_success(self):
        return self._evaluations <= self._max_evaluations and self._absolute_error <= self._absolute_accuracy
