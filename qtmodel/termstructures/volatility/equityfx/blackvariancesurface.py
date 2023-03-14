from datetime import datetime
from enum import Enum
from typing import List

import numpy as np

from qtmodel.error import qt_require
from qtmodel.math.interpolations.bilinearinterpolation import Bilinear
from qtmodel.math.interpolations.interpolation2d import Interpolation2D
from qtmodel.patterns.visitor import Visitor
from qtmodel.termstructures.volatility.equityfx.blackvoltermstructure import BlackVarianceTermStructure
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class ExtrapolationTypes(Enum):
    ConstantExtrapolation = "ConstantExtrapolation"
    InterpolatorDefaultExtrapolation = "InterpolatorDefaultExtrapolation"


class BlackVarianceSurface(BlackVarianceTermStructure):
    """
    Black volatility surface modelled as variance surface
    This class calculates time/strike dependent Black volatilities
    using as input a matrix of Black volatilities observed in the
    market.

    The calculation is performed interpolating on the variance
    surface.  Bilinear interpolation is used as default; this can
    be changed by the setInterpolation() method.

    todo check time extrapolation
    """

    def __init__(self,
                 reference_date: datetime,
                 cal: Calendar,
                 dates: List[datetime],
                 strikes: List[Real],
                 black_vol_matrix: np.ndarray,
                 day_counter: DayCounter,
                 lower_ex: ExtrapolationTypes = ExtrapolationTypes.InterpolatorDefaultExtrapolation,
                 upper_ex: ExtrapolationTypes = ExtrapolationTypes.InterpolatorDefaultExtrapolation):

        super(BlackVarianceSurface, self).__init__(reference_date=reference_date,
                                                   cal=cal)
        self._day_counter = day_counter
        self._max_date = dates[-1]
        self._strikes = strikes
        self._lower_extrapolation = lower_ex
        self._upper_extrapolation = upper_ex
        self._variance_surface: Interpolation2D = None

        qt_require(len(dates) == black_vol_matrix.shape[1],
                   "mismatch between date vector and vol matrix colums")
        qt_require(len(self._strikes) == black_vol_matrix.shape[0],
                   "mismatch between money-strike vector and vol matrix rows")

        qt_require(dates[0] >= reference_date,
                   "cannot have dates[0] < reference_date")

        self._times = [None] * (len(dates) + 1)
        self._times[0] = 0.0
        self._variances = np.zeros((len(self._strikes), len(dates) + 1))
        for i in range(black_vol_matrix.shape[0]):
            self._variances[i, 0] = 0.0

        for j in range(1, black_vol_matrix.shape[1] + 1):
            self._times[j] = self.time_from_reference(dates[j - 1])
            qt_require(self._times[j] > self._times[j - 1],
                       "dates must be sorted unique!")
            for i in range(black_vol_matrix.shape[0]):
                self._variances[i, j] = self._times[j] * black_vol_matrix[i, j - 1] * black_vol_matrix[i, j - 1]

        # default: bilinear interpolation
        self.set_interpolation(class_type=Bilinear)

    def set_interpolation(self,
                          class_type,
                          interpolator=None):
        if interpolator is None:
            interpolator = class_type()
        self._variance_surface = interpolator.interpolate(self._times,
                                                          self._strikes,
                                                          self._variances)
        self.notify_observers()

    def day_counter(self):
        return self._day_counter

    def max_date(self):
        return self._max_date

    def min_strike(self):
        return self._strikes[0]

    def max_strike(self):
        return self._strikes[1]

    def accept(self, v: Visitor):
        v.visit(self)

    def black_variance_impl(self,
                            t: Real,
                            strike: Real):
        if t == 0.0:
            return 0.0

        # enforce constant extrapolation when required
        if strike < self._strikes[0] and self._lower_extrapolation == ExtrapolationTypes.ConstantExtrapolation:
            strike = self._strikes[0]
        if strike > self._strikes[-1] and self._upper_extrapolation == ExtrapolationTypes.ConstantExtrapolation:
            strike = self._strikes[-1]

        if t <= self._times[-1]:
            return self._variance_surface(t, strike, True)
        else:  # t>self._times[-1] or extrapolate
            return self._variance_surface(self._times[-1], strike, True) * t / self._times[-1]
