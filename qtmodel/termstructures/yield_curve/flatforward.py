from datetime import datetime
from typing import Union

from qtmodel.compounding import Compounding
from qtmodel.error import QTError
from qtmodel.handle import Handle
from qtmodel.interestrate import InterestRate
from qtmodel.patterns.lazyobject import LazyObject
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.yieldtermstructure import YieldTermStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.frequency import Frequency
from qtmodel.types import Real


class FlatForward(YieldTermStructure, LazyObject):
    """ Flat interest-rate curve """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 calendar: Calendar = None,
                 forward: Union[Handle, Real] = None,
                 day_counter: DayCounter = None,
                 compounding: Compounding = Compounding.Continuous,
                 frequency: Frequency = Frequency.Annual):
        if reference_date is not None and forward is not None and \
                day_counter is not None and compounding is not None and \
                frequency is not None and settlement_days is None and \
                calendar is None:
            if isinstance(forward, Handle):
                YieldTermStructure.__init__(self,
                                            reference_date=reference_date,
                                            cal=None,
                                            dc=day_counter)
                LazyObject.__init__(self)
                self._forward = forward
                self._compounding = compounding
                self._frequency = frequency
                self.register_with(self._forward)

            elif isinstance(forward, (int, float)):
                YieldTermStructure.__init__(self,
                                            reference_date=reference_date,
                                            cal=None,
                                            dc=day_counter)
                LazyObject.__init__(self)
                self._forward = SimpleQuote(value=forward)
                self._compounding = compounding
                self._frequency = frequency
            else:
                raise QTError("forward must be handle or real")
        elif reference_date is None and forward is not None and \
                day_counter is not None and compounding is not None and \
                frequency is not None and settlement_days is not None and \
                calendar is not None:
            if isinstance(forward, Handle):
                YieldTermStructure.__init__(self,
                                            settlement_days=settlement_days,
                                            cal=calendar,
                                            dc=day_counter)
                LazyObject.__init__(self)
                self._forward = forward
                self._compounding = compounding
                self._frequency = frequency
                self.register_with(self._forward)
            elif isinstance(forward, (int, float)):
                YieldTermStructure.__init__(self,
                                            settlement_days=settlement_days,
                                            cal=calendar,
                                            dc=day_counter)
                LazyObject.__init__(self)
                self._forward = SimpleQuote(forward)
                self._compounding = compounding
                self._frequency = frequency
            else:
                raise QTError("forward must be handle or real")
        else:
            raise QTError("it's not in the four scenarios")

        self._rate: InterestRate = None

    def compounding(self):
        return self._compounding

    def compounding_frequency(self):
        return self._frequency

    @staticmethod
    def max_date():
        return datetime(2199, 12, 31)

    def update(self):
        LazyObject.update(self)
        YieldTermStructure.update(self)

    def discount_impl(self, t: Real):
        self.calculate()
        return self._rate.discount_factor(t)

    def perform_calculations(self):
        self._rate = InterestRate(r=self._forward.value(),
                                  dc=None,
                                  comp=self._compounding,
                                  freq=self._frequency)
