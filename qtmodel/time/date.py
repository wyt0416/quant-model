import calendar
from datetime import datetime, timedelta

from qtmodel.error import QTError, qt_require
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.weekday import Weekday


class DateTool:
    """
    Date tool class
    """

    @staticmethod
    def advance(date: datetime,
                n: int = None,
                units: TimeUnit = None,
                period: Period = None) -> datetime:
        """
        Add a period to date.
        :param date: datetime
        :param n: int
        :param units: TimeUnit
        :param period: Period
        :return: datetime
        """
        if n is not None and units is not None:
            if units == TimeUnit.Days:
                return date + timedelta(days=n)
            elif units == TimeUnit.Weeks:
                return date + timedelta(weeks=n)
            elif units == TimeUnit.Months:
                day = date.day
                month = date.month + n
                year = date.year
                while month > 12:
                    month -= 12
                    year += 1
                while month < 1:
                    month += 12
                    year -= 1
                month_len = calendar.monthrange(year=year, month=month)[1]
                if day > month_len:
                    day = month_len
                return datetime(year=year, month=month, day=day)
            elif units == TimeUnit.Years:
                day = date.day
                month = date.month
                year = date.year + n
                if day == 29 and month == 2 and not calendar.isleap(year=year):
                    day = 28
                return datetime(year=year, month=month, day=day)
            else:
                raise QTError("undefined time units")
        elif period is not None:
            return DateTool.advance(date=date, n=period.length, units=period.units)
        else:
            raise QTError("n and units must be passed together. If n and units are not passed, period must be passed")

    @staticmethod
    def end_of_month(date: datetime) -> datetime:
        """
        :param date:
        :return:
        """
        month_len = calendar.monthrange(year=date.year, month=date.month)[1]
        this_month_end = datetime(date.year, date.month, month_len)
        return this_month_end

    @staticmethod
    def is_end_of_month(date: datetime) -> bool:
        this_month_end = DateTool.end_of_month(date=date)
        return date == this_month_end

    @staticmethod
    def weekday(date: datetime) -> Weekday:
        """
        :param date: datetime
        :return: Weekday
        """
        w = date.isoweekday()
        return Weekday(w)

    @staticmethod
    def day_of_year(date: datetime) -> int:
        """
        :param date:
        :return:
        """
        return int(date.strftime('%j'))

    @staticmethod
    def nth_weekday(nth: int, weekday: Weekday, year: int, month: int):
        qt_require(nth > 0, "zeroth day of week in a given (month, year) is undefined")
        qt_require(nth < 6, "no more than 5 weekday in a given (month, year)")
        first = datetime(year, month, 1).isoweekday()
        skip = nth - (1 if weekday.value >= first else 0)
        return datetime(year, month, (1 + (weekday.value - first) + skip * 7))

    @staticmethod
    def days_between(date1: datetime, date2: datetime):
        return (date2 - date1).days


if __name__ == '__main__':
    # d1 = datetime(2020, 2, 29)
    # period = Period(n=1, units=TimeUnit.Years)
    # d2 = DateTool.advance(d1, period=period)
    # print(d1)
    # print(d2)
    print(DateTool.nth_weekday(1, Weekday.Monday, 2021, 1))
