from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import List

from qtmodel.types import Real


class StepCondition:
    @abstractmethod
    def apply_to(self, a: List, t: datetime):
        pass


class NullCondition(StepCondition):
    def apply_to(self, unnamed_parameter, unnamed_parameter_2):
        pass


class StepCondition(metaclass=ABCMeta):
    """ condition to be applied at every time step """

    @abstractmethod
    def apply_to(self, a, t: Real):
        pass


class NoneCondition(StepCondition):
    """ null step condition """

    def apply_to(self, a, t: Real):
        pass
