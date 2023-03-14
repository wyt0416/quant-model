from qtmodel.error import qt_require, qt_ensure
from qtmodel.event import SimpleEvent
from qtmodel.exercise import Exercise
from qtmodel.instrument import InstrumentResults
from qtmodel.option import Option, Greeks, OptionArguments
from qtmodel.payoff import Payoff
from qtmodel.pricingengine import GenericEngine, PricingEngineArguments


class MultiAssetOptionEngine(GenericEngine):

    def __init__(self):
        super(MultiAssetOptionEngine, self).__init__(arguments_type=OptionArguments,
                                                     results_type=MultiAssetOptionResults)


class MultiAssetOptionResults(InstrumentResults, Greeks):
    """ Results from single-asset option calculation """

    def reset(self):
        InstrumentResults.reset(self)
        Greeks.reset(self)


class MultiAssetOption(Option):
    """ Base class for options on multiple assets """

    def __init__(self, payoff: Payoff, exercise: Exercise):
        super(MultiAssetOption, self).__init__(payoff=payoff, exercise=exercise)
        self._delta = self._gamma = self._theta = self._vega = self._rho = self._dividend_rho = None

    # name Instrument interface

    def is_expired(self):
        return SimpleEvent(self._exercise.last_date()).has_occurred()

    def delta(self):
        self.calculate()
        qt_require(self._delta is not None, "delta not provided")
        return self._delta

    def gamma(self):
        self.calculate()
        qt_require(self._gamma is not None, "gamma not provided")
        return self._gamma

    def theta(self):
        self.calculate()
        qt_require(self._theta is not None, "theta not provided")
        return self._theta

    def vega(self):
        self.calculate()
        qt_require(self._vega is not None, "vega not provided")
        return self._vega

    def rho(self):
        self.calculate()
        qt_require(self._rho is not None, "rho not provided")
        return self._rho

    def dividend_rho(self):
        self.calculate()
        qt_require(self._dividend_rho is not None, "dividend rho not provided")
        return self._dividend_rho

    def setup_expired(self):
        self._NPV = self._delta = self._gamma = self._theta = self._vega = self._rho = self._dividend_rho = 0.0

    def setup_arguments(self, args: PricingEngineArguments):
        arguments = args if isinstance(args, OptionArguments) else None
        qt_require(arguments is not None, "wrong argument type")

        arguments.payoff = self._payoff
        arguments.exercise = self._exercise

    def fetch_results(self, r: Greeks):
        Option.fetch_results(self, r)
        results = r
        qt_ensure(results is not None, "r must be greeks")
        self._delta = results.delta
        self._gamma = results.gamma
        self._theta = results.theta
        self._vega = results.vega
        self._rho = results.rho
        self._dividend_rho = results.dividend_rho
