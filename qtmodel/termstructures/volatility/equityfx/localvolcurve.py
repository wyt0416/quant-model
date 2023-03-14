import math
import sys

from qtmodel.handle import Handle
from qtmodel.termstructures.volatility.equityfx.localvoltermstructure import LocalVolTermStructure
from qtmodel.types import Real


class LocalVolCurve(LocalVolTermStructure):
    """ Local volatility curve derived from a Black curve """

    def __init__(self, curve: Handle):
        super(LocalVolCurve, self).__init__(bdc=curve.business_day_convention(),
                                            dc=curve.day_counter())
        self._black_variance_curve = curve
        self.register_with(self._black_variance_curve)

    def reference_date(self):
        return self._black_variance_curve.reference_date()

    def calendar(self):
        return self._black_variance_curve.calendar()

    def day_counter(self):
        return self._black_variance_curve.day_counter()

    def max_date(self):
        return self._black_variance_curve.max_date()

    def min_strike(self):
        return -sys.float_info.max

    def max_strike(self):
        return sys.float_info.max

    def local_vol_impl(self, t: Real, dummy: Real):
        dt = (1.0 / 365.0)
        var1 = self._black_variance_curve.black_variance(t, dummy, True)
        var2 = self._black_variance_curve.black_variance(t + dt, dummy, True)
        derivative = (var2 - var1) / dt
        return math.sqrt(derivative)
