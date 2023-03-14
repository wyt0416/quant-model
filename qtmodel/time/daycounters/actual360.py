from datetime import datetime

from qtmodel.time.daycounter import DayCounter


class Actual360(DayCounter):
    def __init__(self, include_last_day: bool = False):
        self.include_last_day = include_last_day

    def name(self):
        return "Actual/360 (inc)" if self.include_last_day else "Actual/360"

    def day_count(self, date1: datetime, date2: datetime):
        return super().day_count(date1=date1, date2=date2) + (1 if self.include_last_day else 0)

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2) / 360
