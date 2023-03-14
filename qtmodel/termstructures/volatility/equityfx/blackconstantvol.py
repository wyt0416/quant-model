import sys
from datetime import datetime
from typing import Union

from qtmodel.error import QTError
from qtmodel.handle import Handle
from qtmodel.patterns.visitor import Visitor
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.volatility.equityfx.blackvoltermstructure import BlackVolatilityTermStructure
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class BlackConstantVol(BlackVolatilityTermStructure):

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 volatility: Union[Real, Handle] = None,
                 dc: DayCounter = None):
        if reference_date is not None and cal is not None and volatility is not None and dc is not None:
            if isinstance(volatility, (int, float)):
                super(BlackConstantVol, self).__init__(reference_date=reference_date,
                                                       cal=cal,
                                                       bdc=BusinessDayConvention.Following,
                                                       dc=dc)
                self._volatility = SimpleQuote(volatility)
            elif isinstance(volatility, Handle):
                super(BlackConstantVol, self).__init__(reference_date=reference_date,
                                                       cal=cal,
                                                       bdc=BusinessDayConvention.Following,
                                                       dc=dc)
                self._volatility = volatility
                self.register_with(self._volatility)
        elif settlement_days is not None and cal is not None and volatility is not None and dc is not None:
            if isinstance(volatility, (int, float)):
                super(BlackConstantVol, self).__init__(settlement_days=settlement_days,
                                                       cal=cal,
                                                       bdc=BusinessDayConvention.Following,
                                                       dc=dc)
                self._volatility = SimpleQuote(volatility)
            elif isinstance(volatility, Handle):
                super(BlackConstantVol, self).__init__(settlement_days=settlement_days,
                                                       cal=cal,
                                                       bdc=BusinessDayConvention.Following,
                                                       dc=dc)
                self._volatility = volatility
                self.register_with(self._volatility)
        else:
            raise QTError("it's not in the four scenarios")

    def max_date(self):
        return datetime(2199, 12, 31)

    def min_strike(self):
        return -sys.float_info.max

    def max_strike(self):
        return sys.float_info.max

    def accept(self, v: Visitor):
        v.visit(self)

    def black_vol_impl(self, t: Real, unnamed_parameter: Real):
        return self._volatility.value()
