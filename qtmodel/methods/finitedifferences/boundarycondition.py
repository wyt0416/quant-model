from abc import ABCMeta, abstractmethod
from enum import Enum

from qtmodel.error import QTError
from qtmodel.methods.finitedifferences.tridiagonaloperator import TridiagonalOperator
from qtmodel.types import Real


class BoundaryConditionSideTypes(Enum):
    Null = "Null"
    Upper = "Upper"
    Lower = "Lower"


class BoundaryCondition(metaclass=ABCMeta):
    """ Abstract boundary condition class for finite difference problems """

    @abstractmethod
    def apply_before_applying(self, x):
        pass

    @abstractmethod
    def apply_after_applying(self, x):
        pass

    @abstractmethod
    def apply_before_solving(self, x, rhs):
        pass

    @abstractmethod
    def apply_after_solving(self, x):
        pass

    @abstractmethod
    def set_time(self, t: Real):
        """ This method sets the current time for time-dependent boundary conditions. """
        pass


class NeumannBC(BoundaryCondition):
    """
    Time-independent boundary conditions for tridiagonal operators
    Neumann boundary condition (i.e., constant derivative)
    """

    def __init__(self, value: Real, side: BoundaryConditionSideTypes):
        self._value = value
        self._side = side

    def apply_before_applying(self, L: TridiagonalOperator):
        if self._side == BoundaryConditionSideTypes.Lower:
            L.set_first_row(-1.0, 1.0)
        elif self._side == BoundaryConditionSideTypes.Upper:
            L.set_last_row(-1.0, 1.0)
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_after_applying(self, u: list):
        if self._side == BoundaryConditionSideTypes.Lower:
            u[0] = u[1] - self._value
        elif self._side == BoundaryConditionSideTypes.Upper:
            u[-1] = u[-2] + self._value
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_before_solving(self, L: TridiagonalOperator, rhs: list):
        if self._side == BoundaryConditionSideTypes.Lower:
            L.set_first_row(-1.0, 1.0)
            rhs[0] = self._value
        elif self._side == BoundaryConditionSideTypes.Upper:
            L.set_last_row(-1.0, 1.0)
            rhs[-1] = self._value
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_after_solving(self, x: list):
        pass

    def set_time(self, t: Real):
        pass


class DirichletBC(BoundaryCondition):
    """
    Neumann boundary condition (i.e., constant value)
    todo generalize to time-dependent conditions.
    """

    def __init__(self, value: Real, side: BoundaryConditionSideTypes):
        self._value = value
        self._side = side

    def apply_before_applying(self, L: TridiagonalOperator):
        if self._side == BoundaryConditionSideTypes.Lower:
            L.set_first_row(1.0, 0.0)
        elif self._side == BoundaryConditionSideTypes.Upper:
            L.set_last_row(0.0, 1.0)
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_after_applying(self, u: list):
        if self._side == BoundaryConditionSideTypes.Lower:
            u[0] = self._value
        elif self._side == BoundaryConditionSideTypes.Upper:
            u[-1] = self._value
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_before_solving(self, L: TridiagonalOperator, rhs: list):
        if self._side == BoundaryConditionSideTypes.Lower:
            L.set_first_row(1.0, 0.0)
            rhs[0] = self._value
        elif self._side == BoundaryConditionSideTypes.Upper:
            L.set_last_row(0.0, 1.0)
            rhs[-1] = self._value
        else:
            QTError("unknown side for Neumann boundary condition")

    def apply_after_solving(self, x: list):
        pass

    def set_time(self, t: Real):
        pass
