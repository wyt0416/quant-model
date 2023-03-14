""" Basket option on a number of assets """
from abc import ABC, abstractmethod
from typing import List

from qtmodel.error import qt_require
from qtmodel.exercise import Exercise
from qtmodel.instruments.multiassetoption import MultiAssetOption, MultiAssetOptionResults
from qtmodel.option import OptionArguments
from qtmodel.payoff import Payoff
from qtmodel.pricingengine import GenericEngine
from qtmodel.types import Real


class BasketPayoff(Payoff):
    def __init__(self, p: Payoff):
        self._base_payoff = p

    def name(self):
        return self._base_payoff.name()

    def description(self):
        return self._base_payoff.description()

    def __call__(self, price: Real = None, a: List = None):
        if price is not None:
            return self._base_payoff(price)
        elif a:
            return self._base_payoff(self.accumulate(a))

    @abstractmethod
    def accumulate(self, a: List):
        pass

    def base_payoff(self):
        return self._base_payoff


class MinBasketPayoff(BasketPayoff):
    def __init__(self, p: Payoff):
        super(MinBasketPayoff, self).__init__(p=p)

    def accumulate(self, a: List):
        return min(a)


class MaxBasketPayoff(BasketPayoff):
    def __init__(self, p: Payoff):
        super(MaxBasketPayoff, self).__init__(p=p)

    def accumulate(self, a):
        return max(a)


class AverageBasketPayoff(BasketPayoff):

    def __init__(self, p: Payoff, a: List = None, n: int = None):
        if a is not None:
            super(AverageBasketPayoff, self).__init__(p=p)
            self._weights = a
        elif n is not None:
            super(AverageBasketPayoff, self).__init__(p=p)
            self._weights = [1.0 / n] * n

    def accumulate(self, a: List):
        return sum(i * j for i, j in zip(self._weights, a[:len(self._weights)]))


class SpreadBasketPayoff(BasketPayoff):
    def __init__(self, p):
        super(SpreadBasketPayoff, self).__init__(p=p)

    def accumulate(self, a: List):
        qt_require(len(a) == 2, "payoff is only defined for two underlyings")
        return a[0] - a[1]


class BasketOptionEngine(GenericEngine, ABC):

    def __init__(self):
        super(BasketOptionEngine, self).__init__(arguments_type=OptionArguments,
                                                 results_type=MultiAssetOptionResults)


class BasketOption(MultiAssetOption):

    def __init__(self, payoff: BasketPayoff, exercise: Exercise):
        super().__init__(payoff, exercise)
