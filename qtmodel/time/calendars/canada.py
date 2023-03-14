from datetime import datetime, timedelta

from qtmodel.error import QTError
from qtmodel.time.calendar import Calendar, CalendarTypes, EasterMondayTypes
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday

canada_calendar_types = [CalendarTypes.CANADA_SETTLEMENT, CalendarTypes.CANADA_TSX]

class Canada(Calendar):
    """
    Canadian calendar
    Banking holidays
    (data from <http://www.bankofcanada.ca/en/about/holiday.html>):
    Saturdays
    Sundays
    New Year's Day, January 1st (possibly moved to Monday)
    Family Day, third Monday of February (since 2008)
    Good Friday
    Victoria Day, the Monday on or preceding May 24th
    Canada Day, July 1st (possibly moved to Monday)
    Provincial Holiday, first Monday of August
    Labour Day, first Monday of September
    National Day for Truth and Reconciliation, September 30th (possibly moved to Monday)
    Thanksgiving Day, second Monday of October
    Remembrance Day, November 11th (possibly moved to Monday)
    Christmas, December 25th (possibly moved to Monday or Tuesday)
    Boxing Day, December 26th (possibly moved to Monday or Tuesday)

    Holidays for the Toronto stock exchange
    (data from <http://www.tsx.com/en/about_tsx/market_hours.html>):
    Saturdays
    Sundays
    New Year's Day, January 1st (possibly moved to Monday)
    Family Day, third Monday of February (since 2008)
    Good Friday
    Victoria Day, the Monday on or preceding May 24th
    Canada Day, July 1st (possibly moved to Monday)
    Provincial Holiday, first Monday of August
    Labour Day, first Monday of September
    Thanksgiving Day, second Monday of October
    Christmas, December 25th (possibly moved to Monday or Tuesday)
    Boxing Day, December 26th (possibly moved to Monday or Tuesday)
    """

    added_holidays = set()
    removed_holidays = set()

    def __init__(self, calendar_type: CalendarTypes = CalendarTypes.CANADA_SETTLEMENT):
        if calendar_type not in canada_calendar_types:
            raise QTError("unknown market")
        else:
            super().__init__(calendar_type=calendar_type)

    def _is_business_day(self, date: datetime) -> bool:
        if self.calendar_type == CalendarTypes.CANADA_SETTLEMENT:
            year = date.year
            month = date.month
            weekday = DateTool.weekday(date=date)
            day = date.day
            easter_monday = self.easter_monday(year=year, easter_monday_type=EasterMondayTypes.Western)
            if (self.is_weekend(weekday)
                    # New Year's Day (possibly moved to Monday)
                    or ((day == 1 or ((day == 2 or day == 3) and weekday == Weekday.Monday)) and month == 1)
                    # Family Day (third Monday in February, since 2008)
                    or ((15 <= day <= 21) and weekday == Weekday.Monday and month == 2
                        and year >= 2008)
                    # Good Friday
                    or (date == easter_monday - timedelta(days=3))
                    # The Monday on or preceding 24 May (Victoria Day)
                    or (17 < day <= 24 and weekday == Weekday.Monday and month == 5)
                    # July 1st, possibly moved to Monday (Canada Day)
                    or ((day == 1 or ((day == 2 or day == 3) and weekday == Weekday.Monday)) and month == 7)
                    # first Monday of August (Provincial Holiday)
                    or (day <= 7 and weekday == Weekday.Monday and month == 8)
                    # first Monday of September (Labor Day)
                    or (day <= 7 and weekday == Weekday.Monday and month == 9)
                    # September 30th, possibly moved to Monday
                    # (National Day for Truth and Reconciliation, since 2021)
                    or (((day == 30 and month == 9) or (
                            day <= 2 and month == 10 and weekday == Weekday.Monday)) and year >= 2021)
                    # second Monday of October (Thanksgiving Day)
                    or (7 < day <= 14 and weekday == Weekday.Monday and month == 10)
                    # November 11th (possibly moved to Monday)
                    or ((day == 11 or ((day == 12 or day == 13) and weekday == Weekday.Monday))
                        and month == 11)
                    # Christmas (possibly moved to Monday or Tuesday)
                    or ((day == 25 or (day == 27 and (weekday == Weekday.Monday or weekday == Weekday.Tuesday)))
                        and month == 12)
                    # Boxing Day (possibly moved to Monday or Tuesday)
                    or ((day == 26 or (day == 28 and (weekday == Weekday.Monday or weekday == Weekday.Tuesday)))
                        and month == 12)):
                return False  # NOLINT(readability-simplify-boolean-expr)
            return True

        elif self.calendar_type == CalendarTypes.CANADA_TSX:
            year = date.year
            month = date.month
            weekday = DateTool.weekday(date=date)
            day = date.day
            easter_monday = self.easter_monday(year=year, easter_monday_type=EasterMondayTypes.Western)
            if (self.is_weekend(weekday)
                    # New Year's Day (possibly moved to Monday)
                    or ((day == 1 or ((day == 2 or day == 3) and weekday == Weekday.Monday)) and month == 1)
                    # Family Day (third Monday in February, since 2008)
                    or ((15 <= day <= 21) and weekday == Weekday.Monday and month == 2
                        and year >= 2008)
                    # Good Friday
                    or (date == easter_monday - timedelta(days=3))
                    # The Monday on or preceding 24 May (Victoria Day)
                    or (17 < day <= 24 and weekday == Weekday.Monday and month == 5)
                    # July 1st, possibly moved to Monday (Canada Day)
                    or ((day == 1 or ((day == 2 or day == 3) and weekday == Weekday.Monday)) and month == 7)
                    # first Monday of August (Provincial Holiday)
                    or (day <= 7 and weekday == Weekday.Monday and month == 8)
                    # first Monday of September (Labor Day)
                    or (day <= 7 and weekday == Weekday.Monday and month == 9)
                    # second Monday of October (Thanksgiving Day)
                    or (7 < day <= 14 and weekday == Weekday.Monday and month == 10)
                    # Christmas (possibly moved to Monday or Tuesday)
                    or ((day == 25 or (day == 27 and (weekday == Weekday.Monday or weekday == Weekday.Tuesday)))
                        and month == 12)
                    # Boxing Day (possibly moved to Monday or Tuesday)
                    or ((day == 26 or (day == 28 and (weekday == Weekday.Monday or weekday == Weekday.Tuesday)))
                        and month == 12)):
                return False  # NOLINT(readability-simplify-boolean-expr)
            return True

