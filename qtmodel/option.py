from enum import Enum

from qtmodel.error import qt_require, QTError
from qtmodel.exercise import Exercise
from qtmodel.instrument import Instrument
from qtmodel.payoff import Payoff
from qtmodel.pricingengine import PricingEngineArguments, PricingEngineResults


class OptionTypes(Enum):
    Put = -1
    Call = 1

    def __str__(self):
        if self == OptionTypes.Call:
            return "Call"
        elif self == OptionTypes.Put:
            return "Put"
        else:
            raise QTError("unknown option type")


class OptionArguments(PricingEngineArguments):
    """ basic option arguments """

    def __init__(self):
        self.payoff: Payoff = None
        self.exercise: Exercise = None

    def validate(self):
        qt_require(self.payoff is not None, "no payoff given")
        qt_require(self.exercise is not None, "no exercise given")


class Option(Instrument):
    """ base option class """

    def __init__(self, payoff: Payoff, exercise: Exercise):
        super(Option, self).__init__()
        self._payoff = payoff
        self._exercise = exercise

    def setup_arguments(self, args: PricingEngineArguments):
        args.payoff = self._payoff
        args.exercise = self._exercise

    def payoff(self):
        return self._payoff

    def exercise(self):
        return self._exercise


class Greeks(PricingEngineResults):
    """ additional option results """

    def __init__(self):
        self.delta = self.gamma = self.theta = self.vega = self.rho = self.dividend_rho = None
        self.itm_cash_probability = self.delta_forward = self.elasticity = \
            self.theta_per_day = self.strike_sensitivity = None

    def reset(self):
        self.delta = self.gamma = self.theta = self.vega = self.rho = self.dividend_rho = None
        self.itm_cash_probability = self.delta_forward = self.elasticity = \
            self.theta_per_day = self.strike_sensitivity = None


# class MoreGreeks(PricingEngineResults):
#     """ more additional %option results """
#
#     def __init__(self):
#         self.itm_cash_probability = self.delta_forward = self.elasticity = \
#             self.theta_per_day = self.strike_sensitivity = None
#
#     def reset(self):
#         self.itm_cash_probability = self.delta_forward = self.elasticity = \
#             self.theta_per_day = self.strike_sensitivity = None
