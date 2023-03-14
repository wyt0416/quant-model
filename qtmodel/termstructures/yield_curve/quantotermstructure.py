from qtmodel.compounding import Compounding
from qtmodel.handle import Handle
from qtmodel.termstructures.yield_curve.zeroyieldstructure import ZeroYieldStructure
from qtmodel.time.frequency import Frequency
from qtmodel.types import Real


class QuantoTermStructure(ZeroYieldStructure):

    def __init__(self,
                 underlying_dividend_ts: Handle,
                 risk_free_ts: Handle,
                 foreign_risk_free_ts: Handle,
                 underlying_black_vol_ts: Handle,
                 strike: Real,
                 exch_rate_black_vol_ts: Handle,
                 exch_rate_atmlevel: Real,
                 underlying_exch_rate_correlation: Real):
        super().__init__(underlying_dividend_ts.day_counter())

        self._underlying_dividend_ts = underlying_dividend_ts
        self._risk_free_ts = risk_free_ts
        self._foreign_risk_free_ts = foreign_risk_free_ts
        self._underlying_black_vol_ts = underlying_black_vol_ts
        self._exch_rate_black_vol_ts = exch_rate_black_vol_ts

        self._underlying_exch_rate_correlation = underlying_exch_rate_correlation
        self._strike = strike
        self._exch_rate_atmlevel = exch_rate_atmlevel
        self.register_with(self._underlying_dividend_ts)
        self.register_with(self._risk_free_ts)
        self.register_with(self._foreign_risk_free_ts)
        self.register_with(self._underlying_black_vol_ts)
        self.register_with(self._exch_rate_black_vol_ts)

    def day_counter(self):
        return self._underlying_dividend_ts.day_counter()

    def calendar(self):
        return self._underlying_dividend_ts.calendar()

    def settlement_days(self):
        return self._underlying_dividend_ts.settlement_days()

    def reference_date(self):
        return self._underlying_dividend_ts.reference_date()

    def max_date(self):
        max_date = min(self._underlying_dividend_ts.max_date(), self._risk_free_ts.max_date())
        max_date = min(max_date, self._foreign_risk_free_ts.max_date())
        max_date = min(max_date, self._underlying_black_vol_ts.max_date())
        max_date = min(max_date, self._exch_rate_black_vol_ts.max_date())
        return max_date

    # ! returns the zero yield as seen from the evaluation date

    def zero_yield_impl(self, t):
        return self._underlying_dividend_ts.zero_rate(t=t, comp=Compounding.Continuous, freq=Frequency.NoFrequency,
                                                      extrapolate=True) + self._risk_free_ts.zero_rate(t=t,
                                                                                                       comp=Compounding.Continuous,
                                                                                                       freq=Frequency.NoFrequency,
                                                                                                       extrapolate=True) - self._foreign_risk_free_ts.zero_rate(
            t=t, comp=Compounding.Continuous, freq=Frequency.NoFrequency,
            extrapolate=True) + self._underlying_exch_rate_correlation * self._underlying_black_vol_ts.black_vol(
            maturity=t, strike=self._strike, extrapolate=True) * self._exch_rate_black_vol_ts.black_vol(maturity=t,
                                                                                                        strike=self._exch_rate_atmlevel,
                                                                                                        extrapolate=True)
