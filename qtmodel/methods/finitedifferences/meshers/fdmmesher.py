from abc import ABCMeta, abstractmethod

from qtmodel.methods.finitedifferences.operators.fdmlinearopiterator import FdmLinearOpIterator
from qtmodel.methods.finitedifferences.operators.fdmlinearoplayout import FdmLinearOpLayout


class FdmMesher(metaclass=ABCMeta):

    def __init__(self, layout: FdmLinearOpLayout):
        self._layout = layout

    @abstractmethod
    def dplus(self, iter: FdmLinearOpIterator, direction: int):
        pass

    @abstractmethod
    def dminus(self, iter: FdmLinearOpIterator, direction: int):
        pass

    @abstractmethod
    def location(self, iter: FdmLinearOpIterator, direction: int):
        pass

    @abstractmethod
    def locations(self, direction: int):
        pass

    def layout(self):
        return self._layout
