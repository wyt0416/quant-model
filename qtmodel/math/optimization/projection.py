import copy
from typing import List

from qtmodel.error import qt_require


class Projection:

    def __init__(self, parameter_values: list, fix_parameters: List[bool] = None):
        self._number_of_free_parameters = 0
        self._fixed_parameters = copy.deepcopy(parameter_values)
        self._actual_parameters = copy.deepcopy(parameter_values)
        self._fix_parameters = fix_parameters

        if self._fix_parameters is None:
            self._fix_parameters = [False] * len(self._actual_parameters)

        qt_require(len(self._fixed_parameters) == len(self._fix_parameters),
                   "len(self._fixed_parameters) != len(self._fix_parameters)")

        for fix_parameter in self._fix_parameters:
            if not fix_parameter:
                self._number_of_free_parameters += 1
        qt_require(self._number_of_free_parameters > 0, "number_of_free_parameters==0")

    def map_free_parameters(self, parameter_values: list):
        qt_require(len(parameter_values) == self._number_of_free_parameters,
                   "len(parameter_values)!=self._number_of_free_parameters")
        i = 0
        for j in range(len(self._actual_parameters)):
            if not self._fix_parameters[j]:
                self._actual_parameters[j] = parameter_values[i]
                i += 1

    def project(self, parameters: list):
        """
        returns the subset of free parameters corresponding to set of parameters
        :param parameters:
        :return:
        """
        qt_require(len(parameters) == len(self._fix_parameters),
                   "len(parameters) != len(self._fix_parameters)")
        projected_parameters = [None] * self._number_of_free_parameters
        i = 0
        for j in range(len(self._fix_parameters)):
            if not self._fix_parameters[j]:
                projected_parameters[i] = parameters[j]
                i += 1
        return projected_parameters

    def include(self, projected_parameters: list):
        """
        returns whole set of parameters corresponding to the set of projected parameters
        :param projected_parameters:
        :return:
        """
        qt_require(len(projected_parameters) == self._number_of_free_parameters,
                   "len(projected_parameters) != self._number_of_free_parameters")
        y = copy.deepcopy(self._fixed_parameters)
        i = 0
        for j in range(len(y)):
            if not self._fix_parameters[j]:
                y[j] = projected_parameters[i]
                i += 1
        return y

