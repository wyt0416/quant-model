from datetime import datetime, timedelta

from qtmodel.error import QTError
from qtmodel.time.calendar import Calendar, CalendarTypes, EasterMondayTypes
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday

brazil_calendar_types = [
    CalendarTypes.BRAZIL_SETTLEMENT,
    CalendarTypes.BRAZIL_EXCHANGE
]


class Brazil(Calendar):
    """
    Brazilian calendar
    Banking holidays:
    Saturdays
    Sundays
    New Year's Day, January 1st
    Tiradentes's Day, April 21th
    Labour Day, May 1st
    Independence Day, September 7th
    Nossa Sra. Aparecida Day, October 12th
    All Souls Day, November 2nd
    Republic Day, November 15th
    Christmas, December 25th
    Passion of Christ
    Carnival
    Corpus Christi

    Holidays for the Bovespa stock exchange
    Saturdays
    Sundays
    New Year's Day, January 1st
    Sao Paulo City Day, January 25th
    Tiradentes's Day, April 21th
    Labour Day, May 1st
    Revolution Day, July 9th
    Independence Day, September 7th
    Nossa Sra. Aparecida Day, October 12th
    All Souls Day, November 2nd
    Republic Day, November 15th
    Black Consciousness Day, November 20th (since 2007)
    Christmas Eve, December 24th
    Christmas, December 25th
    Passion of Christ
    Carnival
    Corpus Christi
    the last business day of the year
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self, calendar_type: CalendarTypes = CalendarTypes.BRAZIL_SETTLEMENT):
        if calendar_type not in brazil_calendar_types:
            raise QTError("unknown market")
        else:
            super().__init__(calendar_type=calendar_type)

    def _is_business_day(self, date: datetime) -> bool:
        if self.calendar_type == CalendarTypes.BRAZIL_SETTLEMENT:
            return self._is_business_day_settlement(date=date)
        elif self.calendar_type == CalendarTypes.BRAZIL_EXCHANGE:
            return self._is_business_day_exchange(date=date)

    def _is_business_day_settlement(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        easter_monday = self.easter_monday(year=year,
                                           easter_monday_type=EasterMondayTypes.Western)

        if (self.is_weekend(weekday)
                # New Year's Day
                or (day == 1 and month == 1)
                # Tiradentes Day
                or (day == 21 and month == 4)
                # Labor Day
                or (day == 1 and month == 5)
                # Independence Day
                or (day == 7 and month == 9)
                # Nossa Sra. Aparecida Day
                or (day == 12 and month == 10)
                # All Souls Day
                or (day == 2 and month == 11)
                # Republic Day
                or (day == 15 and month == 11)
                # Christmas
                or (day == 25 and month == 12)
                # Passion of Christ
                or (date == easter_monday - timedelta(days=3))
                # Carnival
                or (date == easter_monday - timedelta(days=49) or date == easter_monday - timedelta(days=48))
                # Corpus Christi
                or (date == easter_monday + timedelta(days=59))):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True

    def _is_business_day_exchange(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        easter_monday = self.easter_monday(year=year,
                                           easter_monday_type=EasterMondayTypes.Western)

        if (self.is_weekend(weekday)
                # New Year's Day
                or (day == 1 and month == 1)
                # Sao Paulo City Day
                or (day == 25 and month == 1)
                # Tiradentes Day
                or (day == 21 and month == 4)
                # Labor Day
                or (day == 1 and month == 5)
                # Revolution Day
                or (day == 9 and month == 7)
                # Independence Day
                or (day == 7 and month == 9)
                # Nossa Sra. Aparecida Day
                or (day == 12 and month == 10)
                # All Souls Day
                or (day == 2 and month == 11)
                # Republic Day
                or (day == 15 and month == 11)
                # Black Consciousness Day
                or (day == 20 and month == 11 and year >= 2007)
                # Christmas Eve
                or (day == 24 and month == 12)
                # Christmas
                or (day == 25 and month == 12)
                # Passion of Christ
                or (date == easter_monday - timedelta(days=3))
                # Carnival
                or (date == easter_monday - timedelta(days=49) or date == easter_monday - timedelta(days=48))
                # Corpus Christi
                or (date == easter_monday + timedelta(days=59))
                # last business day of the year
                or (month == 12 and (day == 31 or (day >= 29 and weekday == Weekday.Friday)))):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True
