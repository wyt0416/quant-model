from abc import ABCMeta

from qtmodel.discretizedasset import DiscretizedAsset
from qtmodel.error import qt_require
from qtmodel.math.array import dot_product
from qtmodel.math.comparison import close
from qtmodel.numericalmethod import Lattice
from qtmodel.patterns.curiouslyrecurring import CuriouslyRecurringTemplate
from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class TreeLattice(Lattice, CuriouslyRecurringTemplate, metaclass=ABCMeta):

    def __init__(self, time_grid: TimeGrid, n: int):
        super(TreeLattice, self).__init__(time_grid=time_grid)
        self._n = n
        qt_require(n > 0, "there is no zeronomial lattice!")
        self._state_prices = [[1.0]]
        self._state_prices_limit = 0

    def initialize(self, asset: DiscretizedAsset, t: Real):
        i = self._t.index(t)
        asset._time = t
        asset.reset(self.impl().size(i))

    def rollback(self, asset: DiscretizedAsset, to: Real):
        self.partial_rollback(asset, to)
        asset.adjust_values()

    def partial_rollback(self, asset: DiscretizedAsset, to: Real):
        begin = asset.time()

        if close(begin, to):
            return

        qt_require(begin > to,
                   f"cannot roll the asset back to {to} (it is already at t = {begin})")

        i_from = int(self._t.index(begin))
        i_to = int(self._t.index(to))

        for i in range(i_from - 1, i_to - 1, -1):
            new_values = [None] * self.impl().size(i)
            self.impl().stepback(i, asset.values(), new_values)
            asset._time = self._t[i]
            asset._values = new_values
            # skip the very last adjustment
            if i != i_to:
                asset.adjust_values()

    def present_value(self, asset: DiscretizedAsset):
        """ Computes the present value of an asset using Arrow-Debrew prices """
        i = self._t.index(asset.time())
        return dot_product(asset.values(), self.state_prices(i))

    def state_prices(self, i: int):
        if i > self._state_prices_limit:
            self.compute_state_prices(i)
        return self._state_prices[i]

    def compute_state_prices(self, until: int):
        for i in range(self._state_prices_limit, until):
            self._state_prices.append([0.0] * self.impl().size(i + 1))
            for j in range(self.impl().size(i)):
                disc = self.impl().discount(i, j)
                state_price = self._state_prices[i][j]
                for l in range(self._n):
                    self._state_prices[i + 1][
                        self.impl().descendant(i, j, l)] += state_price * disc * self.impl().probability(i, j, l)
        self._state_prices_limit = until

    def stepback(self, i: int, values: list, new_values: list):
        for j in range(self.impl().size(i)):
            value = 0.0
            for l in range(self._n):
                value += self.impl().probability(i, j, l) * values[self.impl().descendant(i, j, l)]

            value *= self.impl().discount(i, j)
            new_values[j] = value
