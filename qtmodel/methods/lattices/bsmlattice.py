import math

from qtmodel.methods.lattices.lattice1d import TreeLattice1D
from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class BlackScholesLattice(TreeLattice1D):
    """ Simple binomial lattice approximating the Black-Scholes model """

    def __init__(self,
                 tree,
                 risk_free_rate: Real,
                 end: Real,
                 steps: int):
        super(BlackScholesLattice, self).__init__(TimeGrid(end, steps), 2)
        self._tree = tree
        self._risk_free_rate = risk_free_rate
        self._dt = end / steps
        self._discount = math.exp(-risk_free_rate * self._dt)
        self._pd = tree.probability(0, 0, 0)
        self._pu = tree.probability(0, 0, 1)

    def risk_free_rate(self):
        return self._risk_free_rate

    def dt(self):
        return self._dt

    def size(self, i: int):
        return self._tree.size(i)

    def discount(self, unnamed_parameter: int, unnamed_parameter2: int):
        return self._discount

    def stepback(self, i: int, values: list, new_values: list):
        for j in range(self.size(i)):
            new_values[j] = (self._pd * values[j] + self._pu * values[j + 1]) * self._discount

    def underlying(self, i: int, index: int):
        return self._tree.underlying(i, index)

    def descendant(self, i: int, index: int, branch: int):
        return self._tree.descendant(i, index, branch)

    def probability(self, i: int, index: int, branch: int):
        return self._tree.probability(i, index, branch)
