import sys
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List

from qtmodel.error import qt_require, QTError
from qtmodel.exercise import ExerciseTypes
from qtmodel.math.comparison import close_enough
from qtmodel.numericalmethod import Lattice
from qtmodel.types import Real


class CouponAdjustment(Enum):
    """ Indicates if a coupon should be adjusted in pre_adjust_values() or post_adjust_values(). """
    pre = "pre"
    post = "post"


class DiscretizedAsset(metaclass=ABCMeta):
    """ Discretized asset class used by numerical methods """

    def __init__(self):
        self._latest_pre_adjustment = self._latest_post_adjustment = sys.float_info.max
        self._time = self._values = self._method = None

    def time(self):
        return self._time

    def values(self):
        return self._values

    def method(self):
        return self._method

    def initialize(self, method: Lattice, t: Real):
        self._method = method
        self._method.initialize(self, t)

    def rollback(self, to: Real):
        self._method.rollback(self, to)

    def partial_rollback(self, to: Real):
        self._method.partial_rollback(self, to)

    def present_value(self):
        return self._method.present_value(self)

    @abstractmethod
    def reset(self, size: int):
        """
        This method should initialize the asset values to an Array
        of the given size and with values depending on the
        particular asset.
        :param size:
        :return:
        """
        pass

    def pre_adjust_values(self):
        if not close_enough(self.time(), self._latest_pre_adjustment):
            self.pre_adjust_values_impl()
            self._latest_pre_adjustment = self.time()

    def post_adjust_values(self):
        """
        This method will be invoked after rollback and after any
        other asset had their chance to look at the values. For
        instance, payments happening at the present time (and therefore
        not included in an option to be exercised at this time) will be
        added here.

        This method is not virtual; derived classes must override
        the protected postAdjustValuesImpl() method instead.
        :return:
        """
        if not close_enough(self.time(), self._latest_post_adjustment):
            self.post_adjust_values_impl()
            self._latest_post_adjustment = self.time()

    def adjust_values(self):
        """ This method performs both pre- and post-adjustment """
        self.pre_adjust_values()
        self.post_adjust_values()

    @abstractmethod
    def mandatory_times(self) -> list:
        """
        This method returns the times at which the numerical
        method should stop while rolling back the asset. Typical
        examples include payment times, exercise times and such.

        The returned values are not guaranteed to be sorted.
        :return:
        """
        pass

    def is_on_time(self, t: Real):
        """ This method checks whether the asset was rolled at the given time. """
        grid = self.method().time_grid()
        return close_enough(grid[grid.index(t)], self.time())

    def pre_adjust_values_impl(self):
        """ This method performs the actual pre-adjustment """
        pass

    def post_adjust_values_impl(self):
        """ This method performs the actual post-adjustment """
        pass


class DiscretizedDiscountBond(DiscretizedAsset):
    """ Useful discretized discount bond asset """

    def reset(self, size: int):
        self._values = [1.0] * size

    def mandatory_times(self):
        return []


class DiscretizedOption(DiscretizedAsset):
    """ Discretized option on a given asset """

    def __init__(self,
                 underlying: DiscretizedAsset,
                 exercise_type: ExerciseTypes,
                 exercise_times: List[Real]):
        super(DiscretizedOption, self).__init__()
        self._underlying = underlying
        self._exercise_type = exercise_type
        self._exercise_times = exercise_times

    def reset(self, size: int):
        qt_require(self.method() == self._underlying.method(),
                   "option and underlying were initialized on different methods")
        self._values = [0.0] * size
        self.adjust_values()

    def mandatory_times(self):
        times = self._underlying.mandatory_times()
        # discard negative times...

        i = [k for k in self._exercise_times if k >= 0.0]
        # and add the positive ones
        times.extend(i)
        return times

    def post_adjust_values_impl(self):
        """
        In the real world, with time flowing forward, first
        any payment is settled and only after options can be
        exercised. Here, with time flowing backward, options
        must be exercised before performing the adjustment.
        :return:
        """
        self._underlying.partial_rollback(self.time())
        self._underlying.pre_adjust_values()
        if self._exercise_type == ExerciseTypes.American:
            if self._exercise_times[0] <= self._time <= self._exercise_times[1]:
                self.apply_exercise_condition()
        elif self._exercise_type == ExerciseTypes.Bermudan or self._exercise_type == ExerciseTypes.European:
            for i in range(len(self._exercise_times)):
                t = self._exercise_times[i]
                if t >= 0.0 and self.is_on_time(t):
                    self.apply_exercise_condition()
        else:
            QTError("invalid exercise type")

        self._underlying.post_adjust_values()

    def apply_exercise_condition(self):
        for i in range(len(self._values)):
            self._values[i] = max(self._underlying.values()[i], self._values[i])
