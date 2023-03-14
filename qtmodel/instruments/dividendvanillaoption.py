from datetime import datetime
from typing import List

from qtmodel.cashflows.dividend import dividend_vector
from qtmodel.error import qt_require, QTError
from qtmodel.exercise import Exercise, ExerciseTypes
from qtmodel.instruments.impliedvolatility import ImpliedVolatilityHelper
from qtmodel.instruments.oneassetoption import OneAssetOption
from qtmodel.instruments.payoffs import StrikedTypePayoff
from qtmodel.pricingengines.vanilla.analyticdividendeuropeanengine import AnalyticDividendEuropeanEngine
from qtmodel.pricingengines.vanilla.fdblackscholesvanillaengine import FdBlackScholesVanillaEngine
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.types import Real


class DividendVanillaOption(OneAssetOption):
    """ Single-asset vanilla option (no barriers) with discrete dividends """

    def __init__(self,
                 payoff: StrikedTypePayoff,
                 exercise: Exercise,
                 dividend_dates: List[datetime],
                 dividends: List[Real]):
        super(DividendVanillaOption, self).__init__(payoff=payoff, exercise=exercise)
        self._cash_flow = dividend_vector(dividend_dates, dividends)

    def implied_volatility(self,
                           target_value: Real,
                           process: GeneralizedBlackScholesProcess,
                           accuracy: Real = 1.0e-4,
                           max_evaluations: int = 100,
                           min_vol: Real = 1.0e-7,
                           max_vol: Real = 4.0):
        qt_require(not self.is_expired(), "option expired")

        vol_quote = SimpleQuote()

        new_process = ImpliedVolatilityHelper.clone(process, vol_quote)

        # engines are built-in for the time being
        engine = None
        if self._exercise.type() == ExerciseTypes.European:
            engine = AnalyticDividendEuropeanEngine(new_process)
        elif self._exercise.type() == ExerciseTypes.American:
            engine = FdBlackScholesVanillaEngine(new_process)
        elif self._exercise.type() == ExerciseTypes.Bermudan:
            QTError("engine not available for Bermudan option with dividends")
        else:
            QTError("unknown exercise type")

        return ImpliedVolatilityHelper.calculate(instrument=self,
                                                 engine=engine,
                                                 vol_quote=vol_quote,
                                                 target_value=target_value,
                                                 accuracy=accuracy,
                                                 max_evaluations=max_evaluations,
                                                 min_vol=min_vol,
                                                 max_vol=max_vol)
