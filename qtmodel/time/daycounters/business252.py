from collections import defaultdict
from datetime import datetime

from qtmodel.time.calendar import Calendar
from qtmodel.time.calendars.brazil import Brazil
from qtmodel.time.date import DateTool
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.timeunit import TimeUnit


class Business252(DayCounter):

    def __init__(self, calendar: Calendar = Brazil()):
        self.calendar = calendar
        self.cache = defaultdict(dict)
        self.outer_cache = defaultdict(int)

    def name(self):
        return f"Business/252({self.calendar.name()})"

    def day_count(self, date1: datetime, date2: datetime):
        if self.same_month(date1, date2) or date1 >= date2:
            # we treat the case of date1 > date2 here, since we'd need a
            # second cache to get it right (our cached figures are
            # for first included, last excluded and might have to be
            # changed going the other way.)
            return self.calendar.business_days_between(date1, date2)
        elif self.same_year(date1, date2):
            total = 0
            # first, we get to the beginning of next month.
            d = DateTool.advance(date=datetime(date1.year, date1.month, 1), n=1, units=TimeUnit.Months)
            total += self.calendar.business_days_between(date1, d)
            # then, we add any whole months (whose figures might be
            # cached already) in the middle of our period.
            while not self.same_month(d, date2):
                total += self._business_days(cache=self.cache,
                                             calendar=self.calendar,
                                             year=d.year,
                                             month=d.month)
                d = DateTool.advance(date=d, n=1, units=TimeUnit.Months)
            # finally, we get to the end of the period.
            total += self.calendar.business_days_between(d, date2)
            return total
        else:
            total = 0
            # first, we get to the beginning of next year.
            # The first bit gets us to the end of this month...
            d = DateTool.advance(date=datetime(date1.year, date1.month, 1), n=1, units=TimeUnit.Months)
            total += self.calendar.business_days_between(date1, d)
            # ...then we add any remaining months, possibly cached
            m = date1.month + 1
            while m <= 12:
                total += self._business_days(cache=self.cache,
                                             calendar=self.calendar,
                                             year=d.year,
                                             month=m)
                m += 1
            # then, we add any whole year in the middle of our period.
            d = datetime(date1.year+1, 1, 1)
            while not self.same_year(d, date2):
                total += self._business_days(outer_cache=self.outer_cache,
                                             cache=self.cache,
                                             calendar=self.calendar,
                                             year=d.year)
                d = DateTool.advance(date=d, n=1, units=TimeUnit.Years)
            # finally, we get to the end of the period.
            # First, we add whole months...
            m = 1
            while m < date2.month:
                total += self._business_days(cache=self.cache,
                                             calendar=self.calendar,
                                             year=date2.year,
                                             month=m)
                m += 1
            # ...then the last bit.
            d = datetime(date2.year, date2.month, 1)
            total += self.calendar.business_days_between(d, date2)
            return total

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2) / 252.0

    def same_year(self, date1: datetime, date2: datetime):
        return date1.year == date2.year

    def same_month(self, date1: datetime, date2: datetime):
        return date1.year == date2.year and date1.month == date2.month

    def _business_days(self,
                       cache: dict,
                       calendar: Calendar,
                       year: int,
                       month: int = None,
                       outer_cache: dict = None):
        if outer_cache is None and month is not None:
            if cache[year].get(month) is None:
                # calculate and store.
                date1 = datetime(year, month, 1)
                date2 = DateTool.advance(date=date1, n=1, units=TimeUnit.Months)
                cache[year][month] = calendar.business_days_between(begin=date1, end=date2)
            return cache[year][month]
        elif outer_cache is not None:
            if outer_cache[year] == 0:
                # calculate and store.
                total = 0
                i = 1
                while i <= 12:
                    total += self._business_days(cache=cache,
                                                 calendar=calendar,
                                                 year=year,
                                                 month=i)
                    i += 1
                outer_cache[year] = total
            return outer_cache[year]

