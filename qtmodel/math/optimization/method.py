from abc import ABCMeta, abstractmethod

from qtmodel.math.optimization.endcriteria import EndCriteria, EndCriteriaTypes
from qtmodel.math.optimization.problem import Problem


class OptimizationMethod(metaclass=ABCMeta):
    """ Abstract class for constrained optimization method """

    @abstractmethod
    def minimize(self, p: Problem, end_criteria: EndCriteria) -> EndCriteriaTypes:
        """
        minimize the optimization problem P
        :param p:
        :param end_criteria:
        :return:
        """
        pass
