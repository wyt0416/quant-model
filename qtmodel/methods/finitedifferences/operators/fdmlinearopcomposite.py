import copy
from abc import ABCMeta, abstractmethod
from typing import List

import numpy as np

from qtmodel.error import QTError
from qtmodel.methods.finitedifferences.operators.fdmlinearop import FdmLinearOp
from qtmodel.types import Real


class FdmLinearOpComposite(FdmLinearOp, metaclass=ABCMeta):

    @abstractmethod
    def size(self):
        pass

    @abstractmethod
    def set_time(self, t1: Real, t2: Real):
        pass

    @abstractmethod
    def apply_mixed(self, r: list):
        pass

    @abstractmethod
    def apply_direction(self, direction: int, r: list):
        pass

    @abstractmethod
    def solve_splitting(self, direction: int, r: list, s: Real):
        pass

    @abstractmethod
    def preconditioner(self, r: list, s: Real):
        pass

    def to_matrix_decomp(self) -> List[np.ndarray]:
        QTError(" ublas representation is not implemented")

    def to_matrix(self):
        dcmp = self.to_matrix_decomp()
        result = copy.deepcopy(dcmp[0])
        for i in range(1, len(dcmp)):
            result += dcmp[i]
        return result
