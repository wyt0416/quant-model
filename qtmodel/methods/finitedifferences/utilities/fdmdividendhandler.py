import copy
import math
from datetime import datetime

from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.math.interpolations.linearinterpolation import LinearInterpolation
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.stepcondition import StepCondition
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class FdmDividendHandler(StepCondition):

    def __init__(self,
                 schedule: DividendSchedule,
                 mesher: FdmMesher,
                 reference_date: datetime,
                 day_counter: DayCounter,
                 equity_direction: int):
        self._x = [None] * mesher.layout().dim()[equity_direction]
        self._mesher = mesher
        self._equity_direction = equity_direction

        self._dividends = []
        self._dividend_dates = []
        self._dividend_times = []
        for iter in schedule:
            self._dividends.append(iter.amount())
            self._dividend_dates.append(iter.date())
            self._dividend_times.append(day_counter.year_fraction(reference_date, iter.date()))

        tmp = self._mesher.locations(equity_direction)
        spacing = self._mesher.layout().spacing()[equity_direction]
        for i in range(len(self._x)):
            self._x[i] = math.exp(tmp[i * spacing])

    def apply_to(self, a: list, t: Real):
        a_copy = copy.deepcopy(a)

        if t in self._dividend_times:
            iter = self._dividend_times.index(t)
            dividend = self._dividends[iter]

            if self._mesher.layout().dim().size() == 1:
                interp = LinearInterpolation(self._x, a_copy)
                for k in range(len(self._x)):
                    a[k] = interp(max(self._x[0], self._x[k] - dividend), True)
            else:
                tmp = [None] * self._x.size()
                x_spacing = self._mesher.layout().spacing()[self._equity_direction]

                for i in range(self._mesher.layout().dim().size()):
                    if i != self._equity_direction:
                        y_spacing = self._mesher.layout().spacing()[i]
                        for j in range(self._mesher.layout().dim()[i]):
                            for k in range(len(self._x)):
                                index = j * y_spacing + k * x_spacing
                                tmp[k] = a_copy[index]

                            interp = LinearInterpolation(self._x, tmp)
                            for k in range(len(self._x)):
                                index = j * y_spacing + k * x_spacing
                                a[index] = interp(
                                    max(self._x[0], self._x[k] - dividend), True)

    def dividend_times(self):
        return self._dividend_times

    def dividend_dates(self):
        return self._dividend_dates

    def dividends(self):
        return self._dividends
