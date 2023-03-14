import math

from qtmodel.compounding import Compounding
from qtmodel.error import qt_require
from qtmodel.exercise import ExerciseTypes
from qtmodel.instruments.dividendvanillaoptionEngine import DividendVanillaOptionEngine
from qtmodel.pricingengines.blackcalculator import BlackCalculator
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.time.frequency import Frequency


class AnalyticDividendEuropeanEngine(DividendVanillaOptionEngine):
    """ Analytic pricing engine for European options with discrete dividends """

    def __init__(self, process: GeneralizedBlackScholesProcess):
        super(AnalyticDividendEuropeanEngine, self).__init__()
        self._process = process
        self.register_with(self._process)

    def calculate(self):
        qt_require(self._arguments.exercise.type() == ExerciseTypes.European,
                   "not an European option")

        payoff = self._arguments.payoff
        qt_require(payoff, "non-striked payoff given")

        settlement_date = self._process.risk_free_rate().reference_date()
        riskless = 0.0
        for i in range(len(self._arguments.cash_flow)):
            cash_flow_date = self._arguments.cash_flow[i].date()

            if settlement_date <= cash_flow_date <= self._arguments.exercise.last_date():
                riskless += self._arguments.cash_flow[i].amount() * self._process.risk_free_rate().discount(
                    cash_flow_date) / self._process.dividend_yield().discount(cash_flow_date)

        spot = self._process.state_variable().value() - riskless
        qt_require(spot > 0.0,
                   "negative or null underlying after subtracting dividends")

        dividend_discount = self._process.dividend_yield().discount(self._arguments.exercise.last_date())
        risk_free_discount = self._process.risk_free_rate().discount(self._arguments.exercise.last_date())
        forward_price = spot * dividend_discount / risk_free_discount

        variance = self._process.black_volatility().black_variance(self._arguments.exercise.last_date(),
                                                                   payoff.strike())

        black = BlackCalculator(payoff=payoff, forward=forward_price, std_dev=math.sqrt(variance),
                                discount=risk_free_discount)

        self._results.value = black.value()
        self._results.delta = black.delta(spot)
        self._results.gamma = black.gamma(spot)

        rfdc = self._process.risk_free_rate().day_counter()
        dydc = self._process.dividend_yield().day_counter()
        voldc = self._process.black_volatility().day_counter()
        t = voldc.year_fraction(self._process.black_volatility().reference_date(),
                                self._arguments.exercise.last_date())
        self._results.vega = black.vega(t)

        delta_theta = 0.0
        delta_rho = 0.0
        for i in range(len(self._arguments.cash_flow)):
            d = self._arguments.cash_flow[i].date()

            if settlement_date <= d <= self._arguments.exercise.last_date():
                delta_theta -= self._arguments.cash_flow[i].amount() * (
                        self._process.risk_free_rate().zero_rate(d=d,
                                                                 day_counter=rfdc,
                                                                 comp=Compounding.Continuous,
                                                                 freq=Frequency.Annual) - self._process.dividend_yield().zero_rate(
                    d=d,
                    day_counter=dydc,
                    comp=Compounding.Continuous,
                    freq=Frequency.Annual)) * self._process.risk_free_rate().discount(
                    d) / self._process.dividend_yield().discount(d)

                t = self._process.time(d)
                delta_rho += self._arguments.cash_flow[i].amount() * t * self._process.risk_free_rate().discount(
                    t) / self._process.dividend_yield().discount(t)

        t = self._process.time(self._arguments.exercise.last_date())
        try:
            self._results._theta = black.theta(spot, t) + delta_theta * black.delta(spot)
        except:
            self._results._theta = None

        self._results.rho = black.rho(t) + delta_rho * black.delta(spot)
