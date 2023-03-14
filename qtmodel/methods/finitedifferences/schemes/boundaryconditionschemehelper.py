from typing import List

from qtmodel.methods.finitedifferences.boundarycondition import BoundaryCondition
from qtmodel.methods.finitedifferences.operators.fdmlinearop import FdmLinearOp
from qtmodel.types import Real


class BoundaryConditionSchemeHelper:

    def __init__(self, bc_set: List[BoundaryCondition]):
        self._bc_set = bc_set

    def apply_before_applying(self, op: FdmLinearOp):
        for i in self._bc_set:
            i.apply_before_applying(op)

    def apply_before_solving(self, op: FdmLinearOp, a: list):
        for i in self._bc_set:
            i.apply_before_solving(op, a)

    def apply_after_applying(self, a: list):
        for i in self._bc_set:
            i.apply_after_applying(a)

    def apply_after_solving(self, a: list):
        for i in self._bc_set:
            i.apply_after_solving(a)

    def set_time(self, t: Real):
        for i in self._bc_set:
            i.set_time(t)
