from abc import ABCMeta, abstractmethod


class FdmLinearOp(metaclass=ABCMeta):

    @abstractmethod
    def apply(self, r: list):
        pass

    @abstractmethod
    def to_matrix(self):
        pass
