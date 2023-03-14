import copy

from qtmodel.methods.finitedifferences.stepcondition import StepCondition
from qtmodel.types import Real


class FdmSnapshotCondition(StepCondition):

    def __init__(self, t: Real):
        self._t = t
        self._values = None

    def apply_to(self, a, t: Real):
        if t == self._t:
            self._values = copy.deepcopy(a)

    def get_time(self):
        return self._t

    def get_values(self):
        return self._values