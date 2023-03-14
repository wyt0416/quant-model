import math
from abc import abstractmethod
from datetime import datetime
from typing import List

from qtmodel.handle import Handle
from qtmodel.termstructures.yieldtermstructure import YieldTermStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class ZeroYieldStructure(YieldTermStructure):

    def __init__(self,
                 ref_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 dc: DayCounter = None,
                 jumps: List[Handle] = None,
                 jump_dates: List[datetime] = None):
        if ref_date is not None and \
                cal is not None and \
                dc is not None and \
                settlement_days is None:
            super(ZeroYieldStructure, self).__init__(reference_date=ref_date,
                                                     cal=cal,
                                                     dc=dc,
                                                     jumps=jumps,
                                                     jump_dates=jump_dates)
        elif settlement_days is not None and \
                cal is not None and \
                dc is not None and \
                ref_date is None:
            super(ZeroYieldStructure, self).__init__(settlement_days=settlement_days,
                                                     cal=cal,
                                                     dc=dc,
                                                     jumps=jumps,
                                                     jump_dates=jump_dates)
        elif dc is not None:
            super(ZeroYieldStructure, self).__init__(dc=dc)

    @abstractmethod
    def zero_yield_impl(self, t: Real):
        pass

    def discount_impl(self, t: Real):
        if t == 0.0:  # this acts as a safe guard in cases where
            return 1.0  # zeroYieldImpl(0.0) would throw.

        r = self.zero_yield_impl(t)
        return math.exp(-r * t)
