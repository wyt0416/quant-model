from qtmodel.error import qt_require, QTError
from qtmodel.exercise import Exercise, ExerciseTypes
from qtmodel.instruments.impliedvolatility import ImpliedVolatilityHelper
from qtmodel.instruments.oneassetoption import OneAssetOption
from qtmodel.instruments.payoffs import StrikedTypePayoff
from qtmodel.pricingengines.vanilla.analyticeuropeanengine import AnalyticEuropeanEngine
from qtmodel.pricingengines.vanilla.fdblackscholesvanillaengine import FdBlackScholesVanillaEngine
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.types import Real


class VanillaOption(OneAssetOption):
    """ Vanilla option (no discrete dividends, no barriers) on a single asset """

    def __init__(self, payoff: StrikedTypePayoff, exercise: Exercise):
        super(VanillaOption, self).__init__(payoff=payoff, exercise=exercise)

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

        engine = None
        # engines are built-in for the time being
        if self._exercise.type() == ExerciseTypes.European:
            engine = AnalyticEuropeanEngine(new_process)
        elif self._exercise.type() == ExerciseTypes.American or self._exercise.type() == ExerciseTypes.Bermudan:
            engine = FdBlackScholesVanillaEngine(new_process)
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
