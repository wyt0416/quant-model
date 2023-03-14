from abc import ABCMeta, abstractmethod
from datetime import datetime

from qtmodel.error import QTError, qt_require
from qtmodel.termstructure import TermStructure
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.period import Period
from qtmodel.types import Real


class VolatilityTermStructure(TermStructure, metaclass=ABCMeta):
    """
    Volatility term structure
    This abstract class defines the interface of concrete
    volatility structures which will be derived from this one.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 bdc: BusinessDayConvention = None,
                 dc: DayCounter = None):

        self._bdc: BusinessDayConvention = None

        # Three scenarios
        # initialize with a fixed reference date
        if reference_date is not None and \
                settlement_days is None:
            TermStructure.__init__(self, reference_date=reference_date, calendar=cal, day_counter=dc)
            self._bdc = bdc
        # calculate the reference date based on the global evaluation date
        elif settlement_days is not None and \
                reference_date is None:
            TermStructure.__init__(self, settlement_days=settlement_days, calendar=cal, day_counter=dc)
            self._bdc = bdc
        elif bdc is not None:
            TermStructure.__init__(self, day_counter=dc)
            self._bdc = bdc
        else:
            raise QTError("it's not in the three scenarios")

    def business_day_convention(self):
        """ the business day convention used in tenor to date conversion """
        return self._bdc

    def option_date_from_tenor(self, p: Period):
        """ period/date conversion """
        # swaption style
        return self.calendar().advance(self.reference_date(),
                                       p,
                                       self.business_day_convention())

    @abstractmethod
    def min_strike(self):
        """ the minimum strike for which the term structure can return vols """
        pass

    @abstractmethod
    def max_strike(self):
        """ the maximum strike for which the term structure can return vols """
        pass

    def check_strike(self, strike: Real, extrapolate: bool):
        """ strike-range check """
        qt_require(extrapolate or self.allows_extrapolation() or (self.min_strike() <= strike <= self.max_strike()),
                   f"strike ({strike}) is outside the curve domain [{self.min_strike()},{self.max_strike()}]")
