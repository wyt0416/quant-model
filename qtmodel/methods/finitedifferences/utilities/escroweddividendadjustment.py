from datetime import datetime
from typing import Callable

from qtmodel.handle import Handle
from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.types import Real


class EscrowedDividendAdjustment:

    def __init__(self,
                 dividend_schedule: DividendSchedule,
                 r_ts: Handle,
                 q_ts: Handle,
                 to_time: Callable[[datetime], Real],
                 maturity: Real):
        self._dividend_schedule = dividend_schedule
        self._r_ts = r_ts
        self._q_ts = q_ts
        self._to_time = to_time
        self._maturity = maturity

    def dividend_adjustment(self, t: Real):
        div_adj = 0.0
        for dividend in self._dividend_schedule:
            div_time = self._to_time(dividend.date())

            if div_time >= t and t <= self._maturity:
                div_adj -= dividend.amount() * self._r_ts.discount(div_time) / self._r_ts.discount(
                    t) * self._q_ts.discount(t) / self._q_ts.discount(div_time)

        return div_adj

    def risk_free_rate(self):
        return self._r_ts

    def dividend_yield(self):
        return self._q_ts
