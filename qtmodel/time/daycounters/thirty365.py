from datetime import datetime

from qtmodel.time.daycounter import DayCounter


class Thirty365(DayCounter):
    def __init__(self):
        pass

    def name(self):
        return "30/365"

    def day_count(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2) / 365.0
