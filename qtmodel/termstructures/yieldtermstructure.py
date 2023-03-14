from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List, Union, Optional

from qtmodel.compounding import Compounding
from qtmodel.error import QTError, qt_require
from qtmodel.handle import Handle
from qtmodel.interestrate import InterestRate
from qtmodel.termstructure import TermStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.date import DateTool
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.frequency import Frequency
from qtmodel.time.period import Period
from qtmodel.types import Real


class YieldTermStructure(TermStructure, metaclass=ABCMeta):
    """
    Interest-rate term structure
    This abstract class defines the interface of concrete
    interest rate structures which will be derived from this one.
    """
    dt = 0.0001

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 dc: DayCounter = None,
                 jumps: List[Handle] = None,
                 jump_dates: List[datetime] = None):
        if reference_date is not None and \
                settlement_days is None:
            super().__init__(reference_date=reference_date, calendar=cal, day_counter=dc)
            self._jumps = jumps or []
            self._jump_dates = jump_dates or []
            self._jump_times: List[Optional[Real]] = [None] * len(self._jump_dates)
            self._n_jumps = len(self._jumps)
            self.set_jumps(self.reference_date())
            for i in range(self._n_jumps):
                self.register_with(self._jumps[i])
        elif settlement_days is not None and \
                reference_date is None:
            super().__init__(settlement_days=settlement_days, calendar=cal, day_counter=dc)
            self._jumps = jumps or []
            self._jump_dates = jump_dates or []
            self._jump_times: List[Optional[Real]] = [None] * len(self._jump_dates)
            self._n_jumps = len(self._jumps)
            self.set_jumps(self.reference_date())
            for i in range(self._n_jumps):
                self.register_with(self._jumps[i])
        elif dc is not None:
            super().__init__(day_counter=dc)
        else:
            raise QTError("it's not in the three scenarios")
        self._latest_reference = None

    def discount(self,
                 d: Union[datetime, Real],
                 extrapolate: bool = False):
        if isinstance(d, datetime):
            return self.discount(self.time_from_reference(d), extrapolate)
        elif isinstance(d, (int, float)):
            self.check_range(t=d, extrapolate=extrapolate)

            if len(self._jumps) == 0:
                return self.discount_impl(d)

            jump_effect = 1.0
            for i in range(self._n_jumps):
                if 0 < self._jump_times[i] < d:
                    qt_require(self._jumps[i].is_valid(),
                               f"invalid jump quote index: {i}")
                    this_jump = self._jumps[i].value()
                    qt_require(this_jump > 0.0,
                               f"invalid jump value index: {i}; value: {this_jump}")
                    jump_effect *= this_jump
            return jump_effect * self.discount_impl(d)

    @abstractmethod
    def discount_impl(self, t: Real):
        """ discount factor calculation """
        pass

    def set_jumps(self, reference_date: datetime):
        if len(self._jump_dates) == 0 and len(self._jumps) != 0:  # turn of year dates
            self._jump_dates: List[Optional[datetime]] = [None] * self._n_jumps
            self._jump_times: List[Optional[Real]] = [None] * self._n_jumps
            y = reference_date.year
            for i in range(self._n_jumps):
                self._jump_dates[i] = datetime(y + i, 12, 31)
        else:  # fixed dates
            qt_require(len(self._jump_dates) == self._n_jumps,
                       f"mismatch between number of jumps ({self._n_jumps}) and jump dates ({len(self._jump_dates)})")

        for i in range(self._n_jumps):
            self._jump_times[i] = self.time_from_reference(self._jump_dates[i])
        self._latest_reference = reference_date

    def zero_rate(self,
                  d: datetime = None,
                  t: Real = None,
                  day_counter: DayCounter = None,
                  comp: Compounding = None,
                  freq: Frequency = Frequency.Annual,
                  extrapolate: bool = False):
        if d is not None and day_counter is not None and \
                comp is not None and freq is not None and \
                extrapolate is not None:
            if d == self.reference_date():
                compound = 1.0 / self.discount(self.dt, extrapolate)
                # t has been calculated with a possibly different daycounter
                # but the difference should not matter for very small times
                return InterestRate.implied_rate(compound=compound,
                                                 result_dc=day_counter,
                                                 comp=comp,
                                                 freq=freq,
                                                 t=self.dt)
            compound = 1.0 / self.discount(d, extrapolate)
            return InterestRate.implied_rate(compound=compound,
                                             result_dc=day_counter,
                                             comp=comp,
                                             freq=freq,
                                             d1=self.reference_date(),
                                             d2=d)
        elif t is not None and comp is not None and \
                freq is not None and extrapolate is not None:
            if t == 0.0:
                t = self.dt
            compound = 1.0 / self.discount(t, extrapolate)
            return InterestRate.implied_rate(compound=compound,
                                             result_dc=self.day_counter(),
                                             comp=comp,
                                             freq=freq,
                                             t=t)
        else:
            raise QTError("it's not in the two scenarios")

    def forward_rate(self,
                     d1: datetime = None,
                     d2: datetime = None,
                     t1: Real = None,
                     t2: Real = None,
                     d: datetime = None,
                     p: Period = None,
                     day_counter: DayCounter = None,
                     comp: Compounding = None,
                     freq: Frequency = Frequency.Annual,
                     extrapolate: bool = False):
        if d1 is not None and d2 is not None and \
                day_counter is not None and comp is not None and \
                freq is not None and extrapolate is not None:
            if d1 == d2:
                self.check_range(d=d1, extrapolate=extrapolate)
                t1 = max(self.time_from_reference(d1) - self.dt / 2.0, 0.0)
                t2 = t1 + self.dt
                compound = self.discount(t1, True) / self.discount(t2, True)
                # times have been calculated with a possibly different daycounter
                # but the difference should not matter for very small times
                return InterestRate.implied_rate(compound=compound,
                                                 result_dc=day_counter,
                                                 comp=comp,
                                                 freq=freq,
                                                 t=self.dt)
            qt_require(d1 < d2, f"{d1} later than {d2}")
            compound = self.discount(d1, extrapolate) / self.discount(d2, extrapolate)
            return InterestRate.implied_rate(compound=compound,
                                             result_dc=day_counter,
                                             comp=comp,
                                             freq=freq,
                                             d1=d1,
                                             d2=d2)
        elif t1 is not None and t2 is not None and \
                comp is not None and freq is not None and \
                extrapolate is not None:
            if t2 == t1:
                self.check_range(t=t1, extrapolate=extrapolate)
                t1 = max(t1 - self.dt / 2.0, 0.0)
                t2 = t1 + self.dt
                compound = self.discount(t1, True) / self.discount(t2, True)
            else:
                qt_require(t2 > t1, f"t2 ({t2}) < t1 ({t2})")
                compound = self.discount(t1, extrapolate) / self.discount(t2, extrapolate)
            return InterestRate.implied_rate(compound=compound,
                                             result_dc=self.day_counter(),
                                             comp=comp,
                                             freq=freq,
                                             t=t2 - t1)
        elif d is not None and p is not None and \
                day_counter is not None and comp is not None and \
                freq is not None and extrapolate is not None:
            return self.forward_rate(d1=d,
                                     d2=DateTool.advance(date=d, period=p),
                                     day_counter=day_counter,
                                     comp=comp,
                                     freq=freq,
                                     extrapolate=extrapolate)
        else:
            raise QTError("it's not in the three scenarios")

    def jump_dates(self):
        return self._jump_dates

    def jump_times(self):
        return self._jump_times

    def update(self):
        super(YieldTermStructure, self).update()
        new_reference = None
        try:
            new_reference = self.reference_date()
            if new_reference != self._latest_reference:
                self.set_jumps(new_reference)
        except Exception as e:
            if new_reference is None:
                # the curve couldn't calculate the reference
                # date. Most of the times, this is because some
                # underlying handle wasn't set, so we can just absorb
                # the exception and continue; the jumps will be set
                # correctly when a valid underlying is set.
                return
            else:
                # something else happened during the call to
                # set_jumps(), so we let the exception bubble up.
                raise e
