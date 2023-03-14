from abc import ABCMeta

from qtmodel.error import qt_require
from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.instruments.oneassetoption import OneAssetOptionResults
from qtmodel.option import OptionArguments
from qtmodel.pricingengine import GenericEngine
from qtmodel.utilities.dataformatters import IO


class DividendVanillaOptionArguments(OptionArguments):
    """ Arguments for dividend vanilla option calculation """

    def __init__(self):
        super(DividendVanillaOptionArguments, self).__init__()
        self.cash_flow: DividendSchedule = []

    def validate(self):
        super(DividendVanillaOptionArguments, self).validate()
        exercise_date = self.exercise.last_date()
        for i in range(len(self.cash_flow)):
            qt_require(self.cash_flow[i].date() <= exercise_date,
                       f"the {IO.ordinal(i + 1)} dividend date ({self.cash_flow[i].date()}) is later than the exercise date ({exercise_date})")


class DividendVanillaOptionEngine(GenericEngine, metaclass=ABCMeta):
    """ Dividend-vanilla-option engine base class """

    def __init__(self):
        super(DividendVanillaOptionEngine, self).__init__(arguments_type=DividendVanillaOptionArguments,
                                                          results_type=OneAssetOptionResults)