from datetime import datetime

from qtmodel.time.date import DateTool
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.daycounters.thirty360 import Thirty360, Thirty360ConventionTypes


class SimpleDayCounter(DayCounter):
    """
    Simple day counter for reproducing theoretical calculations.
    This day counter tries to ensure that whole-month distances
    are returned as a simple fraction, i.e., 1 year = 1.0,
    6 months = 0.5, 3 months = 0.25 and so forth.
    warning this day counter should be used together with
    NullCalendar, which ensures that dates at whole-month
    distances share the same day of month. It is <b>not</b>
    guaranteed to work with any other calendar.
    """

    def __init__(self):
        self.fallback = Thirty360(convention=Thirty360ConventionTypes.BondBasis)

    def name(self):
        return "Simple"

    def day_count(self, date1: datetime, date2: datetime):
        return self.fallback.day_count(date1=date1, date2=date2)

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        day1 = date1.day
        day2 = date2.day

        if (day1 == day2 or
                # e.g., Aug 30 -> Feb 28 ?
                (day1 > day2 and DateTool.is_end_of_month(date2)) or
                # e.g., Feb 28 -> Aug 30 ?
                (day1 < day2 and DateTool.is_end_of_month(date1))):

            return date2.year - date1.year + (date2.month - date1.month) / 12.0

        else:
            return self.fallback.year_fraction(date1, date2)
