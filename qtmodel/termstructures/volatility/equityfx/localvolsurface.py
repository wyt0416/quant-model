import math
from typing import Union

from qtmodel.error import QTError, qt_ensure
from qtmodel.handle import Handle
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.volatility.equityfx.localvoltermstructure import LocalVolTermStructure
from qtmodel.types import Real


class LocalVolSurface(LocalVolTermStructure):
    """
    Local volatility surface derived from a Black vol surface
    For details about this implementation refer to
    "Stochastic Volatility and Local Volatility," in
    "Case Studies and Financial Modelling Course Notes," by
    Jim Gatheral, Fall Term, 2003

    see www.math.nyu.edu/fellows_fin_math/gatheral/Lecture1_Fall02.pdf
    """

    def __init__(self,
                 black_ts: Handle,
                 risk_free_ts: Handle,
                 dividend_ts: Handle,
                 underlying: Union[Handle, Real]):
        if isinstance(underlying, Handle):
            super(LocalVolSurface, self).__init__(bdc=black_ts.business_day_convention(),
                                                  dc=black_ts.day_counter())
            self._black_ts = black_ts
            self._risk_free_ts = risk_free_ts
            self._dividend_ts = dividend_ts
            self._underlying = underlying
            self.register_with(self._black_ts)
            self.register_with(self._risk_free_ts)
            self.register_with(self._dividend_ts)
            self.register_with(self._underlying)
        elif isinstance(underlying, Real):
            super(LocalVolSurface, self).__init__(bdc=black_ts.business_day_convention(),
                                                  dc=black_ts.day_counter())
            self._black_ts = black_ts
            self._risk_free_ts = risk_free_ts
            self._dividend_ts = dividend_ts
            self._underlying = SimpleQuote(underlying)
            self.register_with(self._black_ts)
            self.register_with(self._risk_free_ts)
            self.register_with(self._dividend_ts)
        else:
            raise QTError("underlying must be handle or real")

    def reference_date(self):
        return self._black_ts.reference_date()

    def day_counter(self):
        return self._black_ts.day_counter()

    def max_date(self):
        return self._black_ts.max_date()

    def min_strike(self):
        return self._black_ts.min_strike()

    def max_strike(self):
        return self._black_ts.max_strike()

    def local_vol_impl(self, t: Real, underlying_level: Real):
        dr = self._risk_free_ts.discount(t, True)
        dq = self._dividend_ts.discount(t, True)
        forward_value = self._underlying.value() * dq / dr

        # strike derivatives
        strike = underlying_level
        y = math.log(strike / forward_value)
        dy = y * 0.0001 if (abs(y) > 0.001) else 0.000001
        strikep = strike * math.exp(dy)
        strikem = strike / math.exp(dy)
        w = self._black_ts.black_variance(t, strike, True)
        wp = self._black_ts.black_variance(t, strikep, True)
        wm = self._black_ts.black_variance(t, strikem, True)
        dwdy = (wp - wm) / (2.0 * dy)
        d2wdy2 = (wp - 2.0 * w + wm) / (dy * dy)

        # time derivative
        if t == 0.0:
            dt = 0.0001
            drpt = self._risk_free_ts.discount(t + dt, True)
            dqpt = self._dividend_ts.discount(t + dt, True)
            strikept = strike * dr * dqpt / (drpt * dq)

            wpt = self._black_ts.black_variance(t + dt, strikept, True)
            qt_ensure(wpt >= w,
                      f"decreasing variance at strike {strike} between time {t} and time {t + dt}")
            dwdt = (wpt - w) / dt
        else:
            dt = min(0.0001, t / 2.0)
            drpt = self._risk_free_ts.discount(t + dt, True)
            drmt = self._risk_free_ts.discount(t - dt, True)
            dqpt = self._dividend_ts.discount(t + dt, True)
            dqmt = self._dividend_ts.discount(t - dt, True)

            strikept = strike * dr * dqpt / (drpt * dq)
            strikemt = strike * dr * dqmt / (drmt * dq)

            wpt = self._black_ts.black_variance(t + dt, strikept, True)
            wmt = self._black_ts.black_variance(t - dt, strikemt, True)

            qt_ensure(wpt >= w,
                      f"decreasing variance at strike {strike} between time {t} and time {t + dt}")
            qt_ensure(w >= wmt,
                      f"decreasing variance at strike {strike} between time {t - dt} and time {t}")

            dwdt = (wpt - wmt) / (2.0 * dt)

        if dwdy == 0.0 and d2wdy2 == 0.0:  # avoid /w where w might be 0.0
            return math.sqrt(dwdt)
        else:
            den1 = 1.0 - y / w * dwdy
            den2 = 0.25 * (-0.25 - 1.0 / w + y * y / w / w) * dwdy * dwdy
            den3 = 0.5 * d2wdy2
            den = den1 + den2 + den3
            result = dwdt / den

            qt_ensure(result >= 0.0,
                      f"negative local vol^2 at strike {strike} and time {t}; the black vol surface is not smooth enough")

            return math.sqrt(result)
