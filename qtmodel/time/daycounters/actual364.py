from datetime import datetime

from qtmodel.time.daycounter import DayCounter


class Actual364(DayCounter):
    def __init__(self):
        pass

    def name(self):
        return "Actual/364"

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2)/364











