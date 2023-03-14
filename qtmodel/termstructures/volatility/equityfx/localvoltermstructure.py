from abc import ABCMeta, abstractmethod
from datetime import datetime

from qtmodel.error import QTError
from qtmodel.patterns.visitor import Visitor
from qtmodel.termstructures.voltermstructure import VolatilityTermStructure
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class LocalVolTermStructure(VolatilityTermStructure, metaclass=ABCMeta):
    """
    This abstract class defines the interface of concrete
    local-volatility term structures which will be derived from this one.

    Volatilities are assumed to be expressed on an annual basis.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 bdc: BusinessDayConvention = BusinessDayConvention.Following,
                 dc: DayCounter = None):

        # initialize with a fixed reference date
        if reference_date is not None and \
                settlement_days is None:
            VolatilityTermStructure.__init__(self, reference_date=reference_date, cal=cal, bdc=bdc, dc=dc)
        # calculate the reference date based on the global evaluation date
        elif settlement_days is not None and \
                cal is not None and \
                reference_date is None:
            VolatilityTermStructure.__init__(self, settlement_days=settlement_days, cal=cal, bdc=bdc, dc=dc)
        else:
            VolatilityTermStructure.__init__(self, bdc=bdc, dc=dc)

    def local_vol(self,
                  d: datetime = None,
                  t: Real = None,
                  underlying_level: Real = None,
                  extrapolate: bool = False):
        if d is not None and t is None and underlying_level is not None:
            self.check_range(d=d, extrapolate=extrapolate)
            self.check_strike(strike=underlying_level, extrapolate=extrapolate)
            t = self.time_from_reference(date=d)
            return self.local_vol_impl(t=t, strike=underlying_level)
        elif t is not None and d is None and underlying_level is not None:
            self.check_range(t=t, extrapolate=extrapolate)
            self.check_strike(strike=underlying_level, extrapolate=extrapolate)
            return self.local_vol_impl(t, underlying_level)
        else:
            raise QTError("it's not in the two scenarios")

    @abstractmethod
    def local_vol_impl(self,
                       t: Real,
                       strike: Real):
        """ local vol calculation """
        pass

    def accept(self, v: Visitor):
        v.visit(self)
