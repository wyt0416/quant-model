from abc import ABCMeta, abstractmethod

from qtmodel.patterns.visitor import Visitor
from qtmodel.types import Real


class Payoff(metaclass=ABCMeta):
    """ Abstract base class for option payoffs """

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def description(self):
        pass

    @abstractmethod
    def __call__(self, price: Real):
        pass

    def accept(self, v: Visitor):
        v.visit(self)
