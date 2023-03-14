from datetime import datetime, timedelta

from qtmodel.time.calendar import Calendar, CalendarTypes, EasterMondayTypes
from qtmodel.time.date import DateTool


class TARGET(Calendar):
    """
    TARGET calendar
    Holidays (see http://www.ecb.int):
    Saturdays
    Sundays
    New Year's Day, January 1st
    Good Friday (since 2000)
    Easter Monday (since 2000)
    Labour Day, May 1st (since 2000)
    Christmas, December 25th
    Day of Goodwill, December 26th (since 2000)
    December 31st (1998, 1999, and 2001)
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self):
        super().__init__(calendar_type=CalendarTypes.TARGET)

    def _is_business_day(self, date: datetime) -> bool:
        """
        :param date:
        :return:
        """
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        easter_monday = self.easter_monday(year=year,
                                           easter_monday_type=EasterMondayTypes.Western)
        if (self.is_weekend(weekday)
                # New Year's Day
                or (day == 1 and month == 1)
                # Good Friday
                or (date == easter_monday - timedelta(days=3) and year >= 2000)
                # Easter Monday
                or (date == easter_monday and year >= 2000)
                # Labour Day
                or (day == 1 and month == 5 and year >= 2000)
                # Christmas
                or (day == 25 and month == 12)
                # Day of Goodwill
                or (day == 26 and month == 12 and year >= 2000)
                # December 31st, 1998, 1999, and 2001 only
                or (day == 31 and month == 12 and
                    (year == 1998 or year == 1999 or year == 2001))):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True
