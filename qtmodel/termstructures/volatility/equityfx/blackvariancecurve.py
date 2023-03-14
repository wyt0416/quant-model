import sys
from datetime import datetime
from typing import List, Optional

from qtmodel.error import qt_require
from qtmodel.math.interpolation import Interpolation
from qtmodel.math.interpolations.linearinterpolation import Linear
from qtmodel.termstructures.volatility.equityfx.blackvoltermstructure import BlackVarianceTermStructure
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class BlackVarianceCurve(BlackVarianceTermStructure):
    """
    Black volatility curve modelled as variance curve
    This class calculates time-dependent Black volatilities using
    as input a vector of (ATM) Black volatilities observed in the
    market.

    The calculation is performed interpolating on the variance curve.
    Linear interpolation is used as default; this can be changed
    by the setInterpolation() method.

    For strike dependence, see BlackVarianceSurface.

    todo check time extrapolation
    """

    def __init__(self,
                 reference_date: datetime,
                 dates: List[datetime],
                 black_vol_curve: List[Real],
                 day_counter: DayCounter,
                 force_monotone_variance: bool = True):
        super(BlackVarianceCurve, self).__init__(reference_date=reference_date)
        self._day_counter = day_counter
        self._max_date = dates[-1]
        self._variance_curve: Interpolation = None

        _dates_len = len(dates)
        _black_vol_curve_len = len(black_vol_curve)
        qt_require(_dates_len == _black_vol_curve_len,
                   "mismatch between date list and black vol list")

        # cannot have dates[0]==reference_date, since the
        # value of the vol at dates[0] would be lost
        # (variance at reference_date must be zero)
        qt_require(dates[0] > reference_date,
                   "cannot have dates[0] <= reference_date")

        self._variances: List[Optional[Real]] = [None] * (_dates_len + 1)
        self._times: List[Optional[Real]] = [None] * (_dates_len + 1)
        self._variances[0] = 0.0
        self._times[0] = 0.0
        for j in range(1, _black_vol_curve_len + 1):
            self._times[j] = self.time_from_reference(dates[j - 1])
            qt_require(self._times[j] > self._times[j - 1],
                       "dates must be sorted unique!")
            self._variances[j] = self._times[j] * black_vol_curve[j - 1] * black_vol_curve[j - 1]
            qt_require(self._variances[j] >= self._variances[j - 1] or not force_monotone_variance,
                       "variance must be non-decreasing")

        # default: linear interpolation
        self.set_interpolation(Linear())

    def set_interpolation(self, interpolator):
        self._variance_curve = interpolator.interpolate(self._times, self._variances)
        self._variance_curve.update()
        self.notify_observers()

    def day_counter(self):
        return self._day_counter

    def max_date(self):
        return self._max_date

    def min_strike(self):
        return -sys.float_info.max

    def max_strike(self):
        return sys.float_info.max

    def black_variance_impl(self, t: Real, unnamed_parameter: Real):
        if t <= self._times[-1]:
            return self._variance_curve(t, True)
        else:
            # extrapolate with flat vol
            return self._variance_curve(self._times[-1], True) * t / self._times[-1]
