from qtmodel.error import qt_require, qt_ensure
from qtmodel.event import SimpleEvent
from qtmodel.exercise import Exercise
from qtmodel.instrument import InstrumentResults
from qtmodel.option import Option, Greeks, OptionArguments
from qtmodel.payoff import Payoff
from qtmodel.pricingengine import GenericEngine


class OneAssetOptionEngine(GenericEngine):

    def __init__(self):
        super(OneAssetOptionEngine, self).__init__(arguments_type=OptionArguments,
                                                   results_type=OneAssetOptionResults)


class OneAssetOptionResults(InstrumentResults, Greeks):
    """ Results from single-asset option calculation """

    def reset(self):
        InstrumentResults.reset(self)
        Greeks.reset(self)


class OneAssetOption(Option):
    """ Base class for options on a single asset """

    def __init__(self, payoff: Payoff, exercise: Exercise):
        super(OneAssetOption, self).__init__(payoff=payoff, exercise=exercise)
        self._delta = self._delta_forward = self._elasticity = self._gamma = self._theta = \
        self._theta_per_day = self._vega = self._rho = self._dividend_rho = self._strike_sensitivity = \
        self._itm_cash_probability = None

    def is_expired(self):
        return SimpleEvent(self._exercise.last_date()).has_occurred()

    def delta(self):
        self.calculate()
        qt_require(self._delta is not None, "delta not provided")
        return self._delta

    def delta_forward(self):
        self.calculate()
        qt_require(self._delta_forward is not None, "forward delta not provided")
        return self._delta_forward

    def elasticity(self):
        self.calculate()
        qt_require(self._elasticity is not None, "elasticity not provided")
        return self._elasticity

    def gamma(self):
        self.calculate()
        qt_require(self._gamma is not None, "gamma not provided")
        return self._gamma

    def theta(self):
        self.calculate()
        qt_require(self._theta is not None, "theta not provided")
        return self._theta

    def theta_per_day(self):
        self.calculate()
        qt_require(self._theta_per_day is not None, "theta per-day not provided")
        return self._theta_per_day

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

    def strike_sensitivity(self):
        self.calculate()
        qt_require(self._strike_sensitivity is not None,
                   "strike sensitivity not provided")
        return self._strike_sensitivity

    def itm_cash_probability(self):
        self.calculate()
        qt_require(self._itm_cash_probability is not None,
                   "in-the-money cash probability not provided")
        return self._itm_cash_probability

    def setup_expired(self):
        Option.setup_expired(self)
        self._delta = self._delta_forward = self._elasticity = self._gamma = self._theta = \
        self._theta_per_day = self._vega = self._rho = self._dividend_rho = \
        self._strike_sensitivity = self._itm_cash_probability = 0.0

    def fetch_results(self, r: Greeks):
        Option.fetch_results(self, r)
        results = r
        qt_ensure(results is not None, "no greeks returned from pricing engine")
        # no check on null values - just copy.
        # this allows:
        # a) to decide in derived options what to do when null
        # results are returned (throw? numerical calculation?)
        # b) to implement slim engines which only calculate the
        # value---of course care must be taken not to call
        # the greeks methods when using these.
        self._delta = results.delta
        self._gamma = results.gamma
        self._theta = results.theta
        self._vega = results.vega
        self._rho = results.rho
        self._dividend_rho = results.dividend_rho

        more_results = r
        qt_ensure(more_results is not None, "no more greeks returned from pricing engine")
        # no check on null values - just copy.
        # this allows:
        # a) to decide in derived options what to do when null
        # results are returned (throw? numerical calculation?)
        # b) to implement slim engines which only calculate the
        # value---of course care must be taken not to call
        # the greeks methods when using these.

        self._delta_forward = more_results.delta_forward
        self._elasticity = more_results.elasticity
        self._theta_per_day = more_results.theta_per_day
        self._strike_sensitivity = more_results.strike_sensitivity
        self._itm_cash_probability = more_results.itm_cash_probability
