import math
from enum import Enum

from qtmodel.error import qt_require
from qtmodel.math.distributions.binomialdistribution import peizer_pratt_method2_inversion
from qtmodel.methods.lattices.tree import Tree
from qtmodel.stochasticprocess import StochasticProcess1D
from qtmodel.types import Real


class Branches(Enum):
    branches = 2


class BinomialTree(Tree):
    """ Binomial tree base class """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int):
        super(BinomialTree, self).__init__(steps + 1)
        self._x0 = process.x0()
        self._dt = end / steps
        self._drift_per_step = process.drift(0.0, self._x0) * self._dt

    def size(self, i: int):
        return i + 1

    def descendant(self, unnamed_parameter: int, index: int, branch: int):
        return index + branch


class EqualProbabilitiesBinomialTree(BinomialTree):
    """ Base class for equal probabilities binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int):
        super(EqualProbabilitiesBinomialTree, self).__init__(process, end, steps)
        self._up = 0

    def underlying(self, i: int, index: int):
        j = 2 * int(index) - int(i)
        # exploiting the forward value tree centering
        return self._x0 * math.exp(i * self._drift_per_step + j * self._up)

    def probability(self, unnamed_parameter: int, unnamed_parameter2: int, unnamed_parameter3: int):
        return 0.5


class EqualJumpsBinomialTree(BinomialTree):
    """ Base class for equal jumps binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int):
        super(EqualJumpsBinomialTree, self).__init__(process, end, steps)
        self._dx = 0
        self._pu = 0
        self._pd = 0

    def underlying(self, i: int, index: int):
        j = 2 * int(index) - int(i)
        # exploiting equal jump and the self._x0 tree centering
        return self._x0 * math.exp(j * self._dx)

    def probability(self, unnamed_parameter: int, unnamed_parameter2: int, branch: int):
        return self._pu if branch == 1 else self._pd


class JarrowRudd(EqualProbabilitiesBinomialTree):
    """ Jarrow-Rudd (multiplicative) equal probabilities binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(JarrowRudd, self).__init__(process, end, steps)
        # drift removed
        self._up = process.std_deviation(0.0, self._x0, self._dt)


class CoxRossRubinstein(EqualJumpsBinomialTree):
    """ Cox-Ross-Rubinstein (multiplicative) equal jumps binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(CoxRossRubinstein, self).__init__(process, end, steps)
        self._dx = process.std_deviation(0.0, self._x0, self._dt)
        self._pu = 0.5 + 0.5 * self._drift_per_step / self._dx
        self._pd = 1.0 - self._pu

        qt_require(self._pu <= 1.0, "negative probability")
        qt_require(self._pu >= 0.0, "negative probability")


class AdditiveEQPBinomialTree(EqualProbabilitiesBinomialTree):
    """ Additive equal probabilities binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(AdditiveEQPBinomialTree, self).__init__(process, end, steps)
        self._up = - 0.5 * self._drift_per_step + 0.5 * math.sqrt(
            4.0 * process.variance(0.0, self._x0, self._dt) - 3.0 * self._drift_per_step * self._drift_per_step)


class Trigeorgis(EqualJumpsBinomialTree):
    """ Trigeorgis (additive equal jumps) binomial tree """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(Trigeorgis, self).__init__(process, end, steps)

        self._dx = math.sqrt(process.variance(0.0, self._x0, self._dt) + self._drift_per_step * self._drift_per_step)
        self._pu = 0.5 + 0.5 * self._drift_per_step / self._dx
        self._pd = 1.0 - self._pu

        qt_require(self._pu <= 1.0, "negative probability")
        qt_require(self._pu >= 0.0, "negative probability")


class Tian(BinomialTree):
    """ Tian tree: third moment matching, multiplicative approach """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(Tian, self).__init__(process, end, steps)
        q = math.exp(process.variance(0.0, self._x0, self._dt))
        r = math.exp(self._drift_per_step) * math.sqrt(q)

        self._up = 0.5 * r * q * (q + 1 + math.sqrt(q * q + 2 * q - 3))
        self._down = 0.5 * r * q * (q + 1 - math.sqrt(q * q + 2 * q - 3))

        self._pu = (r - self._down) / (self._up - self._down)
        self._pd = 1.0 - self._pu

        qt_require(self._pu <= 1.0, "negative probability")
        qt_require(self._pu >= 0.0, "negative probability")

    def underlying(self, i: int, index: int):
        return self._x0 * math.pow(self._down, int(i) - int(index)) * math.pow(self._up, index)

    def probability(self, unnamed_parameter: int, unnamed_parameter2: int, branch: int):
        return self._pu if branch == 1 else self._pd


class LeisenReimer(BinomialTree):
    """ Leisen & Reimer tree: multiplicative approach """

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(LeisenReimer, self).__init__(process, end, steps if (steps % 2) != 0 else (steps + 1))
        qt_require(strike > 0.0, "strike must be positive")
        odd_steps = steps if (steps % 2) != 0 else (steps + 1)
        variance = process.variance(0.0, self._x0, end)
        ermqdt = math.exp(self._drift_per_step + 0.5 * variance / odd_steps)
        d2 = (math.log(self._x0 / strike) + self._drift_per_step * odd_steps) / math.sqrt(variance)
        self._pu = peizer_pratt_method2_inversion(d2, odd_steps)
        self._pd = 1.0 - self._pu
        pdash = peizer_pratt_method2_inversion(d2 + math.sqrt(variance), odd_steps)
        self._up = ermqdt * pdash / self._pu
        self._down = (ermqdt - self._pu * self._up) / (1.0 - self._pu)

    def underlying(self, i: int, index: int):
        return self._x0 * math.pow(self._down, int(i) - int(index)) * math.pow(self._up, index)

    def probability(self, unnamed_parameter: int, unnamed_parameter2: int, branch: int):
        return self._pu if branch == 1 else self._pd


class Joshi4(BinomialTree):

    def __init__(self,
                 process: StochasticProcess1D,
                 end: Real,
                 steps: int,
                 strike: Real):
        super(Joshi4, self).__init__(process, end, steps if (steps % 2) != 0 else (steps + 1))

        qt_require(strike > 0.0, "strike must be positive")
        odd_steps = steps if (steps % 2) != 0 else (steps + 1)
        variance = process.variance(0.0, self._x0, end)
        ermqdt = math.exp(self._drift_per_step + 0.5 * variance / odd_steps)
        d2 = (math.log(self._x0 / strike) + self._drift_per_step * odd_steps) / math.sqrt(variance)
        self._pu = self.compute_up_prob((odd_steps - 1.0) / 2.0, d2)
        self._pd = 1.0 - self._pu
        pdash = self.compute_up_prob((odd_steps - 1.0) / 2.0, d2 + math.sqrt(variance))
        self._up = ermqdt * pdash / self._pu
        self._down = (ermqdt - self._pu * self._up) / (1.0 - self._pu)

    def compute_up_prob(self, k: Real, dj: Real):
        alpha = dj / (math.sqrt(8.0))
        alpha2 = alpha * alpha
        alpha3 = alpha * alpha2
        alpha5 = alpha3 * alpha2
        alpha7 = alpha5 * alpha2
        beta = -0.375 * alpha - alpha3
        gamma = (5.0 / 6.0) * alpha5 + (13.0 / 12.0) * alpha3 + (25.0 / 128.0) * alpha
        delta = -0.1025 * alpha - 0.9285 * alpha3 - 1.43 * alpha5 - 0.5 * alpha7
        p = 0.5
        rootk = math.sqrt(k)
        p += alpha / rootk
        p += beta / (k * rootk)
        p += gamma / (k * k * rootk)
        # delete next line to get results for j three tree
        p += delta / (k * k * k * rootk)
        return p

    def underlying(self, i: int, index: int):
        return self._x0 * math.pow(self._down, int(i) - int(index)) * math.pow(self._up, index)

    def probability(self, unnamed_parameter: int, unnamed_parameter2: int, branch: int):
        return self._pu if branch == 1 else self._pd
