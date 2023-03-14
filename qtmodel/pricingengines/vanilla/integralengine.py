import math

from qtmodel.error import qt_require
from qtmodel.exercise import ExerciseTypes
from qtmodel.instruments.oneassetoption import OneAssetOptionEngine
from qtmodel.math.integrals.segmentintegral import SegmentIntegral
from qtmodel.payoff import Payoff
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.types import Real


class Integrand:
    def __init__(self,
                 payoff: Payoff,
                 s0: Real,
                 drift: Real,
                 variance: Real):
        self._payoff = payoff
        self._s0 = s0
        self._drift = drift
        self._variance = variance

    def __call__(self, x: Real):
        temp = self._s0 * math.exp(x)
        result = self._payoff(temp)
        return result * math.exp(-(x - self._drift) * (x - self._drift) / (2.0 * self._variance))


class IntegralEngine(OneAssetOptionEngine):
    """ Pricing engine for European vanilla options using integral approach """

    def __init__(self, process: GeneralizedBlackScholesProcess):
        super(IntegralEngine, self).__init__()
        self._process = process
        self.register_with(self._process)

    def calculate(self):
        qt_require(self._arguments.exercise.type() == ExerciseTypes.European,
                   "not an European Option")

        payoff = self._arguments.payoff
        qt_require(payoff, "non-striked payoff given")

        variance = self._process.black_volatility().black_variance(
            self._arguments.exercise.last_date(), payoff.strike())

        dividend_discount = self._process.dividend_yield().discount(
            self._arguments.exercise.last_date())
        risk_free_discount = self._process.risk_free_rate().discount(self._arguments.exercise.last_date())
        drift = math.log(dividend_discount / risk_free_discount) - 0.5 * variance

        f = Integrand(self._arguments.payoff,
                      self._process.state_variable().value(),
                      drift,
                      variance)
        integrator = SegmentIntegral(5000)

        infinity = 10.0 * math.sqrt(variance)
        self._results.value = self._process.risk_free_rate().discount(
            self._arguments.exercise.last_date()) / math.sqrt(2.0 * math.pi * variance) * integrator(f, drift - infinity, drift + infinity)
