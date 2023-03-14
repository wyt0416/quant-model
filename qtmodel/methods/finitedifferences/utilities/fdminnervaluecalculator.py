import math
from abc import abstractmethod, ABCMeta
from typing import Callable

from qtmodel.instruments.basketoption import BasketPayoff
from qtmodel.math.integrals.simpsonintegral import SimpsonIntegral
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.fdmlinearopiterator import FdmLinearOpIterator
from qtmodel.payoff import Payoff
from qtmodel.types import Real


class MappedPayoff:

    def __init__(self, payoff: Payoff, grid_mapping: Callable[[Real], Real]):
        self.payoff = payoff
        self._grid_mapping = grid_mapping

    def __call__(self, x: Real):
        return self.payoff(self._grid_mapping(x))


class FdmInnerValueCalculator(metaclass=ABCMeta):

    @abstractmethod
    def inner_value(self, iter: FdmLinearOpIterator, t: Real):
        pass

    @abstractmethod
    def avg_inner_value(self, iter: FdmLinearOpIterator, t: Real):
        pass


class FdmCellAveragingInnerValue(FdmInnerValueCalculator):

    def __init__(self,
                 payoff: Payoff,
                 mesher: FdmMesher,
                 direction: int,
                 grid_mapping: Callable[[Real], Real] = lambda x: x):
        self._payoff = payoff
        self._mesher = mesher
        self._direction = direction
        self._grid_mapping = grid_mapping
        self._avg_inner_values = None

    def inner_value(self, iter: FdmLinearOpIterator, unnamed_parameter: Real):
        loc = self._mesher.location(iter, self._direction)
        return self._payoff(self._grid_mapping(loc))

    def avg_inner_value(self, iter: FdmLinearOpIterator, t: Real):
        if self._avg_inner_values is None:
            # calculate caching values
            self._avg_inner_values = [None] * self._mesher.layout().dim()[self._direction]
            initialized = [False] * len(self._avg_inner_values)

            layout = self._mesher.layout()
            end_iter = layout.end()
            i = layout.begin()
            while i != end_iter:
                xn = i.coordinates()[self._direction]
                if not initialized[xn]:
                    initialized[xn] = True
                    self._avg_inner_values[xn] = self.avg_inner_value_calc(i, t)
                i.increment()

        return self._avg_inner_values[iter.coordinates()[self._direction]]

    def avg_inner_value_calc(self, iter, t: Real):
        dim = self._mesher.layout().dim()[self._direction]
        coord = iter.coordinates()[self._direction]

        if coord == 0 or coord == dim - 1:
            return self.inner_value(iter, t)

        loc = self._mesher.location(iter, self._direction)
        a = loc - self._mesher.dminus(iter, self._direction) / 2.0
        b = loc + self._mesher.dplus(iter, self._direction) / 2.0

        f = MappedPayoff(self._payoff, self._grid_mapping)

        try:
            acc = ((f(a) + f(b)) * 5e-5 if (f(a) != 0.0 or f(b) != 0.0) else 1e-4)
            ret_val = SimpsonIntegral(acc, 8)(f, a, b) / (b - a)
        except:
            # use default value
            ret_val = self.inner_value(iter, t)

        return ret_val


class FdmLogInnerValue(FdmCellAveragingInnerValue):
    def __init__(self, payoff: Payoff, mesher: FdmMesher, direction: int):
        super().__init__(payoff, mesher, direction, lambda x: math.exp(x))


class FdmLogBasketInnerValue(FdmInnerValueCalculator):
    def __init__(self, payoff: BasketPayoff, mesher: FdmMesher):
        self._payoff = payoff
        self._mesher = mesher

    def inner_value(self, iter: FdmLinearOpIterator, unnamed_parameter: Real):
        x = [None] * self._mesher.layout().dim().size()
        i = 0
        while i < len(x):
            x[i] = math.exp(self._mesher.location(iter, i))
            i += 1

        return self._payoff(x)

    def avg_inner_value(self, iter: FdmLinearOpIterator, t: Real):
        return self.inner_value(iter, t)
