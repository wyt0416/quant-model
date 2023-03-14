from datetime import datetime

from qtmodel.time.daycounter import DayCounter


class OneDayCounter(DayCounter):
    """1/1 day count convention"""

    def __init__(self):
        pass

    def name(self):
        return "1/1"

    def day_count(self, date1: datetime, date2: datetime):
        return 1 if date2 >= date1 else -1

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2)
