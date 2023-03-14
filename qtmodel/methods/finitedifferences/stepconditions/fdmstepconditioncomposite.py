from datetime import datetime
from typing import List

from qtmodel.error import qt_require
from qtmodel.exercise import Exercise, ExerciseTypes
from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.stepcondition import StepCondition
from qtmodel.methods.finitedifferences.stepconditions.fdmamericanstepcondition import FdmAmericanStepCondition
from qtmodel.methods.finitedifferences.stepconditions.fdmbermudanstepcondition import FdmBermudanStepCondition
from qtmodel.methods.finitedifferences.stepconditions.fdmsnapshotcondition import FdmSnapshotCondition
from qtmodel.methods.finitedifferences.utilities.fdmdividendhandler import FdmDividendHandler
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmInnerValueCalculator
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class FdmStepConditionComposite(StepCondition):

    def __init__(self,
                 stopping_times: List[List[Real]],
                 conditions: List[StepCondition]):
        self._conditions = conditions
        all_stopping_times = []
        for stopping_time in stopping_times:
            all_stopping_times.extend(stopping_time)
        self._stopping_times = all_stopping_times

    def apply_to(self, a: list, t: Real):
        for condition in self._conditions:
            condition.apply_to(a, t)

    def stopping_times(self):
        return self._stopping_times

    def conditions(self):
        return self._conditions

    @staticmethod
    def join_conditions(c1: FdmSnapshotCondition,
                        c2):
        stopping_times = [c2.stopping_times(), [c1.get_time()]]

        conditions = [c2, c1]

        return FdmStepConditionComposite(stopping_times, conditions)

    @staticmethod
    def vanilla_composite(cash_flow: DividendSchedule,
                          exercise: Exercise,
                          mesher: FdmMesher,
                          calculator: FdmInnerValueCalculator,
                          ref_date: datetime,
                          day_counter: DayCounter):
        stopping_times = []
        step_conditions = []

        if len(cash_flow) != 0:
            dividend_condition = FdmDividendHandler(cash_flow, mesher, ref_date, day_counter, 0)
            step_conditions.append(dividend_condition)

            dividend_times = dividend_condition.dividend_times()
            stopping_times.append(dividend_times)

            # smoother convergence behavior with number of time steps
            maturity_time = day_counter.year_fraction(ref_date, exercise.last_date())

            for i in range(len(dividend_times)):
                dividend_times[i] = min(maturity_time, dividend_times[i] + 1e-5)
            stopping_times.append(dividend_times)

        qt_require(exercise.type() == ExerciseTypes.American
                   or exercise.type() == ExerciseTypes.European
                   or exercise.type() == ExerciseTypes.Bermudan,
                   "exercise type is not supported")
        if exercise.type() == ExerciseTypes.American:
            step_conditions.append(FdmAmericanStepCondition(mesher, calculator))
        elif exercise.type() == ExerciseTypes.Bermudan:
            bermudan_condition = FdmBermudanStepCondition(exercise.dates(),
                                                          ref_date, day_counter,
                                                          mesher, calculator)
            step_conditions.append(bermudan_condition)
            stopping_times.append(bermudan_condition.exercise_times())

        return FdmStepConditionComposite(stopping_times, step_conditions)
