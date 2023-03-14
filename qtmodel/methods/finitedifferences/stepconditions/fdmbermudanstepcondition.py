from datetime import datetime
from typing import List

from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.stepcondition import StepCondition
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmInnerValueCalculator
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class FdmBermudanStepCondition(StepCondition):

    def __init__(self,
                 exercise_dates: List[datetime],
                 reference_date: datetime,
                 day_counter: DayCounter,
                 mesher: FdmMesher,
                 calculator: FdmInnerValueCalculator):
        self._mesher = mesher
        self._calculator = calculator
        self._exercise_times = []
        for exercise_date in exercise_dates:
            self._exercise_times.append(day_counter.year_fraction(reference_date, exercise_date))

    def apply_to(self, a: list, t: Real):

        if t in self._exercise_times:

            layout = self._mesher.layout()

            qt_require(layout.size() == len(a),
                       "inconsistent array dimensions")

            end_iter = layout.end()

            dims = layout.dim().size()
            locations = [None] * dims

            iter = layout.begin()
            while iter != end_iter:
                for i in range(dims):
                    locations[i] = self._mesher.location(iter, i)

                inner_value = self._calculator.inner_value(iter, t)
                if inner_value > a[iter.index()]:
                    a[iter.index()] = inner_value
                iter.increment()

    def exercise_times(self):
        return self._exercise_times
