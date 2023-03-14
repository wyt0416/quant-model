from datetime import datetime
from enum import Enum
from typing import List, Optional

from qtmodel.error import qt_require


class ExerciseTypes(Enum):
    American = "American"
    Bermudan = "Bermudan"
    European = "European"


class Exercise:
    """ Base exercise class """

    def __init__(self, type: ExerciseTypes):
        self._type = type
        self._dates = []

    def type(self):
        return self._type

    def date(self, index: int) -> datetime:
        return self._dates[index]

    def dates(self):
        """
        Returns all exercise dates
        :return:
        """
        return self._dates

    def last_date(self) -> datetime:
        return self._dates[-1]


class EarlyExercise(Exercise):
    """
    Early-exercise base class
    The payoff can be at exercise (the default) or at expiry
    """

    def __init__(self, type: ExerciseTypes, payoff_at_expiry: bool = False):
        super(EarlyExercise, self).__init__(type)
        self._payoff_at_expiry = payoff_at_expiry

    def payoff_at_expiry(self) -> bool:
        return self._payoff_at_expiry


class AmericanExercise(EarlyExercise):
    """
    American exercise
    An American option can be exercised at any time between two
    predefined dates; the first date might be omitted, in which
    case the option can be exercised at any time before the expiry.

    todo check that everywhere the American condition is applied
         from earliestDate and not earlier
    """

    def __init__(self,
                 earliest_date: datetime = None,
                 latest_date: datetime = None,
                 payoff_at_expiry: bool = None):
        super(AmericanExercise, self).__init__(ExerciseTypes.American, payoff_at_expiry)
        if earliest_date is not None:
            qt_require(earliest_date <= latest_date,
                       "earliest > latest exercise date")
        self._dates: List[Optional[datetime]] = [None] * 2
        self._dates[0] = earliest_date if earliest_date is not None else datetime(1901, 1, 1)
        self._dates[1] = latest_date


class BermudanExercise(EarlyExercise):
    """
    Bermudan exercise
    A Bermudan option can only be exercised at a set of fixed dates.
    """

    def __init__(self, dates: List[datetime], payoff_at_expiry: bool = False):
        super(BermudanExercise, self).__init__(ExerciseTypes.Bermudan, payoff_at_expiry)
        qt_require(len(dates) > 0, "no exercise date given")
        self._dates = dates
        self._dates.sort()


class EuropeanExercise(Exercise):
    """
    European exercise
    A European option can only be exercised at one (expiry) date.
    """

    def __init__(self, date: datetime):
        super(EuropeanExercise, self).__init__(ExerciseTypes.European)
        self._dates = [date]
