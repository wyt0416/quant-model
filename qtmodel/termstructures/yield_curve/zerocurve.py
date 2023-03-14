from datetime import datetime
from typing import List, Tuple

from qtmodel.compounding import Compounding
from qtmodel.error import QTError, qt_require
from qtmodel.handle import Handle
from qtmodel.interestrate import InterestRate
from qtmodel.math.comparison import close
from qtmodel.termstructures.interpolatedcurve import InterpolatedCurve
from qtmodel.termstructures.yield_curve.zeroyieldstructure import ZeroYieldStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.frequency import Frequency
from qtmodel.types import Real


class InterpolatedZeroCurve(ZeroYieldStructure, InterpolatedCurve):
    """ YieldTermStructure based on interpolation of zero rates """

    def __init__(self,
                 class_type,
                 dates: List[datetime] = None,
                 yields: List[Real] = None,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 day_counter: DayCounter = None,
                 calendar: Calendar = None,
                 jumps: List[Handle] = None,
                 jump_dates: List[datetime] = None,
                 interpolator=None,
                 compounding: Compounding = Compounding.Continuous,
                 frequency: Frequency = Frequency.Annual):
        self._class_type = class_type
        self._dates = None
        if dates is not None and yields is not None:
            if jumps is not None and jump_dates is not None:
                if interpolator is None:
                    interpolator = class_type()
                ZeroYieldStructure.__init__(self,
                                            ref_date=dates[0],
                                            cal=calendar,
                                            dc=day_counter,
                                            jumps=jumps,
                                            jump_dates=jump_dates)
                InterpolatedCurve.__init__(self,
                                           class_type=class_type,
                                           times=[],
                                           data=yields,
                                           interpolator=interpolator)
                self._dates = dates
                self.initialize(compounding, frequency)
            elif interpolator is not None:
                ZeroYieldStructure.__init__(self,
                                            ref_date=dates[0],
                                            cal=calendar,
                                            dc=day_counter)
                InterpolatedCurve.__init__(self,
                                           class_type=class_type,
                                           times=[],
                                           data=yields,
                                           interpolator=interpolator)
                self._dates = dates
                self.initialize(compounding, frequency)
            else:
                raise QTError("it's not in the two scenarios")
        else:
            if interpolator is None:
                interpolator = class_type()

            if reference_date is not None and \
                    settlement_days is None:
                ZeroYieldStructure.__init__(self,
                                            ref_date=reference_date,
                                            cal=None,
                                            dc=day_counter,
                                            jumps=jumps,
                                            jump_dates=jump_dates)
                InterpolatedCurve.__init__(self,
                                           class_type=class_type,
                                           interpolator=interpolator)
            elif settlement_days is not None and \
                    reference_date is None:
                ZeroYieldStructure.__init__(self,
                                            settlement_days=settlement_days,
                                            cal=calendar,
                                            dc=day_counter,
                                            jumps=jumps,
                                            jump_dates=jump_dates)
                InterpolatedCurve.__init__(self,
                                           class_type=class_type,
                                           interpolator=interpolator)
            else:
                ZeroYieldStructure.__init__(self,
                                            dc=day_counter)
                InterpolatedCurve.__init__(self,
                                           class_type=class_type,
                                           interpolator=interpolator)

    def initialize(self,
                   compounding: Compounding,
                   frequency: Frequency):
        qt_require(len(self._dates) >= self._class_type.required_points,
                   "not enough input dates given")
        qt_require(len(self._data) == len(self._dates),
                   "dates/data count mismatch")

        self._times[0] = 0.0
        if compounding != Compounding.Continuous:
            # We also have to convert the first rate.
            # The first time is 0.0, so we can't use it.
            # We fall back to about one day.
            dt = 1.0 / 365
            r = InterestRate(self._data[0], self.day_counter(), compounding, frequency)
            self._data[0] = r.equivalent_rate(comp=Compounding.Continuous,
                                              freq=Frequency.NoFrequency,
                                              t=dt)

        for i in range(1, len(self._dates)):
            qt_require(self._dates[i] > self._dates[i - 1],
                       f"invalid date ({self._dates[i]} vs {self._dates[i - 1]})")
            self._times[i] = self.day_counter().year_fraction(self._dates[0], self._dates[i])
            qt_require(not close(self._times[i], self._times[i - 1]),
                       "two dates correspond to the same time "
                       "under this curve's day count convention")

            # adjusting zero rates to match continuous compounding
            if compounding != Compounding.Continuous:
                r = InterestRate(self._data[i], self.day_counter(), compounding, frequency)
                self._data[i] = r.equivalent_rate(comp=Compounding.Continuous,
                                                  freq=Frequency.NoFrequency,
                                                  t=self._times[i])

        self._interpolation = self._interpolator.interpolate(self._times, self._data)
        self._interpolation.update()

    def zero_yield_impl(self, t: Real):
        if t <= self._times[-1]:
            return self._interpolation(t, True)

        # flat fwd extrapolation
        t_max = self._times[-1]
        z_max = self._data[-1]
        inst_fwd_max = z_max + t_max * self._interpolation.derivative(t_max)
        return (z_max * t_max + inst_fwd_max * (t - t_max)) / t

    def times(self):
        return self._times

    def dates(self):
        return self._dates

    def data(self):
        return self._data

    def zero_rates(self):
        return self._data

    def nodes(self):
        results: List[Tuple[datetime, Real]] = [None] * len(self._dates)
        for i in range(len(self._dates)):
            results[i] = (self._dates[i], self._data[i])
        return results

    def max_date(self):
        if self._max_date is not None:
            return self._max_date
        return self._dates[-1]
