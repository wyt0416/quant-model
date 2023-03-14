import math

from qtmodel.error import qt_require
from qtmodel.exercise import ExerciseTypes
from qtmodel.handle import Handle
from qtmodel.instruments.oneassetoption import OneAssetOptionEngine
from qtmodel.pricingengines.blackcalculator import BlackCalculator
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess


class AnalyticEuropeanEngine(OneAssetOptionEngine):
    """ Pricing engine for European vanilla options using analytical formulae """

    def __init__(self,
                 process: GeneralizedBlackScholesProcess,
                 discount_curve: Handle = None):
        self._discount_curve = Handle()
        if discount_curve is None:
            super(AnalyticEuropeanEngine, self).__init__()
            self._process = process
            self.register_with(self._process)
        else:
            super(AnalyticEuropeanEngine, self).__init__()
            self._process = process
            self._discount_curve = discount_curve
            self.register_with(self._process)
            self.register_with(self._discount_curve)

    def calculate(self):
        # if the discount curve is not specified, we default to the
        # risk free rate curve embedded within the GBM process
        discount_ptr = self._process.risk_free_rate().current_link() if self._discount_curve.empty() else self._discount_curve.current_link()

        qt_require(self._arguments.exercise.type() == ExerciseTypes.European,
                   "not an European option")

        payoff = self._arguments.payoff
        qt_require(payoff, "non-striked payoff given")

        variance = self._process.black_volatility().black_variance(self._arguments.exercise.last_date(),
                                                                   payoff.strike())
        dividend_discount = self._process.dividend_yield().discount(self._arguments.exercise.last_date())
        df = discount_ptr.discount(self._arguments.exercise.last_date())
        risk_free_discount_for_fwd_estimation = self._process.risk_free_rate().discount(
            self._arguments.exercise.last_date())
        spot = self._process.state_variable().value()
        qt_require(spot > 0.0, "negative or null underlying given")
        forward_price = spot * dividend_discount / risk_free_discount_for_fwd_estimation

        black = BlackCalculator(payoff=payoff,
                                forward=forward_price,
                                std_dev=math.sqrt(variance),
                                discount=df)

        self._results.value = black.value()
        self._results.delta = black.delta(spot)
        self._results.delta_forward = black.delta_forward()
        self._results.elasticity = black.elasticity(spot)
        self._results.gamma = black.gamma(spot)

        rfdc = discount_ptr.day_counter()
        divdc = self._process.dividend_yield().day_counter()
        voldc = self._process.black_volatility().day_counter()
        t = rfdc.year_fraction(self._process.risk_free_rate().reference_date(),
                               self._arguments.exercise.last_date())
        self._results.rho = black.rho(t)

        t = divdc.year_fraction(self._process.dividend_yield().reference_date(),
                                self._arguments.exercise.last_date())
        self._results.dividend_rho = black.dividend_rho(t)

        t = voldc.year_fraction(self._process.black_volatility().reference_date(),
                                self._arguments.exercise.last_date())
        self._results.vega = black.vega(t)
        try:
            self._results.theta = black.theta(spot, t)
            self._results.theta_per_day = black.theta_per_day(spot, t)
        except:
            self._results.theta = None
            self._results.theta_per_day = None

        self._results.strike_sensitivity = black.strike_sensitivity()
        self._results.itm_cash_probability = black.itm_cash_probability()

        tte = self._process.black_volatility().time_from_reference(self._arguments.exercise.last_date())
        self._results.additional_results["spot"] = spot
        self._results.additional_results["dividend_discount"] = dividend_discount
        self._results.additional_results["riskFreeDiscount"] = risk_free_discount_for_fwd_estimation
        self._results.additional_results["forward"] = forward_price
        self._results.additional_results["strike"] = payoff.strike()
        self._results.additional_results["volatility"] = math.sqrt(variance / tte)
        self._results.additional_results["timeToExpiry"] = tte
