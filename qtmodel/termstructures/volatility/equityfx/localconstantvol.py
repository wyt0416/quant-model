import sys
from datetime import datetime
from typing import Union

from qtmodel.error import QTError
from qtmodel.handle import Handle
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.volatility.equityfx.localvoltermstructure import LocalVolTermStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class LocalConstantVol(LocalVolTermStructure):
    """
    Constant local volatility, no time-strike dependence
    This class implements the LocalVolatilityTermStructure
    interface for a constant local volatility (no time/asset
    dependence).  Local volatility and Black volatility are the
    same when volatility is at most time dependent, so this class
    is basically a proxy for BlackVolatilityTermStructure.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 calendar: Calendar = None,
                 volatility: Union[Real, Handle] = None,
                 day_counter: DayCounter = None):
        if reference_date is not None and volatility is not None and day_counter is not None:
            if isinstance(volatility, (int, float)):
                super(LocalConstantVol, self).__init__(reference_date=reference_date)
                self._volatility = SimpleQuote(value=volatility)
                self._day_counter = day_counter
            elif isinstance(volatility, Handle):
                super(LocalConstantVol, self).__init__(reference_date=reference_date)
                self._volatility = volatility
                self._day_counter = day_counter
                self.register_with(self._volatility)
            else:
                raise QTError("volatility must be real or handle")
        elif settlement_days is not None and calendar is not None and volatility is not None and \
                day_counter is not None:
            if isinstance(volatility, (int, float)):
                super(LocalConstantVol, self).__init__(settlement_days=settlement_days,
                                                       cal=calendar)
                self._volatility = SimpleQuote(value=volatility)
                self._day_counter = day_counter
            elif isinstance(volatility, Handle):
                super(LocalConstantVol, self).__init__(settlement_days=settlement_days,
                                                       cal=calendar)
                self._volatility = volatility
                self._day_counter = day_counter
                self.register_with(self._volatility)
            else:
                raise QTError("volatility must be real or handle")

    def day_counter(self):
        return self._day_counter

    def max_date(self):
        return datetime(2199, 12, 31)

    def min_strike(self):
        return -sys.float_info.max

    def max_strike(self):
        return sys.float_info.max

    def local_vol_impl(self, unnamed_parameter: Real, unnamed_parameter2: Real):
        return self._volatility.value()
