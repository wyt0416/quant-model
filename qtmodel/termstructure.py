from abc import ABCMeta, abstractmethod
from datetime import datetime

from qtmodel.error import QTError, qt_require
from qtmodel.math.comparison import close_enough
from qtmodel.math.interpolations.extrapolation import Extrapolator
from qtmodel.patterns.observable import Observer, Observable
from qtmodel.settings import Settings
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.timeunit import TimeUnit
from qtmodel.types import Real


class TermStructure(Observer, Observable, Extrapolator, metaclass=ABCMeta):
    """
    Basic term-structure functionality
    There are three ways in which a term structure can keep
    track of its reference date.  The first is that such date
    is fixed; the second is that it is determined by advancing
    the current date of a given number of business days; and
    the third is that it is based on the reference date of
    some other structure.

    In the first case, the constructor taking a date is to be
    used; the default implementation of referenceDate() will
    then return such date. In the second case, the constructor
    taking a number of days and a calendar is to be used;
    referenceDate() will return a date calculated based on the
    current evaluation date, and the term structure and its
    observers will be notified when the evaluation date
    changes. In the last case, the referenceDate() method must
    be overridden in derived classes so that it fetches and
    return the appropriate date.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 calendar: Calendar = None,
                 day_counter: DayCounter = None):
        Observer.__init__(self)
        Observable.__init__(self)
        Extrapolator.__init__(self)

        self._moving = False
        self._updated = True
        self._calendar = None
        self._reference_date = None
        self._settlement_days = None
        self._day_counter = None

        # Three scenarios
        # initialize with a fixed reference date
        if reference_date is not None and \
                settlement_days is None:
            self._calendar = calendar
            self._reference_date = reference_date
            self._day_counter = day_counter
        # calculate the reference date based on the global evaluation date
        elif settlement_days is not None and \
                calendar is not None and \
                reference_date is None:
            self._moving = True
            self._updated = False
            self._calendar = calendar
            self._settlement_days = settlement_days
            self._day_counter = day_counter
            self.register_with(Settings()._evaluation_date.observable)
        else:
            self._day_counter = day_counter

    def day_counter(self):
        """ the day counter used for date/time conversion """
        return self._day_counter

    def time_from_reference(self, date: datetime):
        """ date/time conversion """
        return self.day_counter().year_fraction(self.reference_date(), date)

    def settlement_days(self):
        qt_require(self._settlement_days is not None,
                   "settlement days not provided for this instance")
        return self._settlement_days

    def reference_date(self):
        """ the date at which discount = 1.0 and/or variance = 0.0 """
        if not self._updated:
            today = Settings().evaluation_date
            self._reference_date = self.calendar().advance(today, self.settlement_days(), TimeUnit.Days)
            self._updated = True
        return self._reference_date

    def calendar(self):
        return self._calendar

    @abstractmethod
    def max_date(self):
        """ the latest date for which the curve can return values """
        pass

    def max_time(self):
        """ the latest time for which the curve can return values """
        return self.time_from_reference(self.max_date())

    def update(self):
        if self._moving:
            self._updated = False
        self.notify_observers()

    def check_range(self,
                    d: datetime = None,
                    t: Real = None,
                    extrapolate: bool = None):
        """ date/time-range check """
        if d is not None and extrapolate is not None:
            qt_require(d >= self.reference_date(),
                       f"date ({d}) before reference date ({self.reference_date()})")
            qt_require(extrapolate or self.allows_extrapolation() or d <= self.max_date(),
                       f"date ({d}) is past max curve date ({self.max_date()})")
        elif t is not None and extrapolate is not None:
            qt_require(t >= 0.0,
                       f"negative time ({t}) given")
            qt_require(
                extrapolate or self.allows_extrapolation() or t <= self.max_time() or close_enough(t, self.max_time()),
                f"time ({t}) is past max curve time ({self.max_time()})")
