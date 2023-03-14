from datetime import datetime, timedelta

from qtmodel.error import QTError
from qtmodel.time.calendar import CalendarTypes, Calendar, EasterMondayTypes
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday

us_calendar_types = [
    CalendarTypes.UNITED_STATES_SETTLEMENT,
    CalendarTypes.UNITED_STATES_NYSE,
    CalendarTypes.UNITED_STATES_GOVERNMENT_BOND,
    CalendarTypes.UNITED_STATES_NERC,
    CalendarTypes.UNITED_STATES_LIBOR_IMPACT,
    CalendarTypes.UNITED_STATES_FEDERAL_RESERVE
]


class UnitedStates(Calendar):
    """
    United States Calendar
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self, calendar_type: CalendarTypes):
        if calendar_type not in us_calendar_types:
            raise QTError("unknown market")
        else:
            super().__init__(calendar_type=calendar_type)

    def _is_business_day(self, date: datetime) -> bool:
        """
        :param date:
        :return:
        """
        if self.calendar_type == CalendarTypes.UNITED_STATES_SETTLEMENT:
            return self._is_business_day_us_settlement(date=date)
        elif self.calendar_type == CalendarTypes.UNITED_STATES_LIBOR_IMPACT:
            return self._is_business_day_us_libor_impact(date=date)
        elif self.calendar_type == CalendarTypes.UNITED_STATES_NYSE:
            return self._is_business_day_us_nyse(date=date)
        elif self.calendar_type == CalendarTypes.UNITED_STATES_GOVERNMENT_BOND:
            return self._is_business_day_us_government_bond(date=date)
        elif self.calendar_type == CalendarTypes.UNITED_STATES_NERC:
            return self._is_business_day_us_nerc(date=date)
        elif self.calendar_type == CalendarTypes.UNITED_STATES_FEDERAL_RESERVE:
            return self._is_business_day_us_federal_reserve(date=date)

    def _is_business_day_us_settlement(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        if (self.is_weekend(weekday)
                # New Year's Day (possibly moved to Monday if on Sunday)
                or ((day == 1 or (day == 2 and weekday == Weekday.Monday)) and month == 1)
                # (or to Friday if on Saturday)
                or (day == 31 and weekday == Weekday.Friday and month == 12)
                # Martin Luther King's birthday (third Monday in January)
                or ((15 <= day <= 21) and weekday == Weekday.Monday and month == 1
                    and year >= 1983)
                # Washington's birthday (third Monday in February)
                or self.is_washington_birthday(year, month, weekday, day)
                # Memorial Day (last Monday in May)
                or self.is_memorial_day(year, month, weekday, day)
                # Juneteenth (Monday if Sunday or Friday if Saturday)
                or self.is_juneteenth(year, month, weekday, day)
                # Independence Day (Monday if Sunday or Friday if Saturday)
                or ((day == 4 or (day == 5 and weekday == Weekday.Monday) or
                     (day == 3 and weekday == Weekday.Friday)) and month == 7)
                # Labor Day (first Monday in September)
                or self.is_labor_day(month, weekday, day)
                # Columbus Day (second Monday in October)
                or self.is_columbus_day(year, month, weekday, day)
                # Veteran's Day (Monday if Sunday or Friday if Saturday)
                or self.is_veterans_day(year, month, weekday, day)
                # Thanksgiving Day (fourth Thursday in November)
                or ((22 <= day <= 28) and weekday == Weekday.Thursday and month == 11)
                # Christmas (Monday if Sunday or Friday if Saturday)
                or ((day == 25 or (day == 26 and weekday == Weekday.Monday) or
                     (day == 24 and weekday == Weekday.Friday)) and month == 12)):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True

    def _is_business_day_us_libor_impact(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        if (((day == 5 and weekday == Weekday.Monday) or
             (day == 3 and weekday == Weekday.Friday)) and month == 7 and year >= 2015):
            return True
        return self._is_business_day_us_settlement(date=date)

    def _is_business_day_us_nyse(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        day_of_year = DateTool.day_of_year(date=date)
        easter_monday = self.easter_monday(year=year,
                                           easter_monday_type=EasterMondayTypes.Western)
        if (self.is_weekend(weekday)
                # New Year's Day (possibly moved to Monday if on Sunday)
                or ((day == 1 or (day == 2 and weekday == Weekday.Monday)) and month == 1)
                # Washington's birthday (third Monday in February)
                or self.is_washington_birthday(year=year, month=month, weekday=weekday, day=day)
                # Good Friday
                or (date == easter_monday - timedelta(days=3))
                # Memorial Day (last Monday in May)
                or self.is_memorial_day(year=year, month=month, weekday=weekday, day=day)
                # Juneteenth (Monday if Sunday or Friday if Saturday)
                or self.is_juneteenth(year=year, month=month, weekday=weekday, day=day)
                # Independence Day (Monday if Sunday or Friday if Saturday)
                or ((day == 4 or (day == 5 and weekday == Weekday.Monday) or
                     (day == 3 and weekday == Weekday.Friday)) and month == 7)
                # Labor Day (first Monday in September)
                or self.is_labor_day(month=month, weekday=weekday, day=day)
                # Thanksgiving Day (fourth Thursday in November)
                or ((22 <= day <= 28) and weekday == Weekday.Thursday and month == 11)
                # Christmas (Monday if Sunday or Friday if Saturday)
                or ((day == 25 or (day == 26 and weekday == Weekday.Monday) or
                     (day == 24 and weekday == Weekday.Friday)) and month == 12)):
            return False

        if (year >= 1998 and 15 <= day <= 21
                and weekday == Weekday.Monday and month == 1):
            # Martin Luther King's birthday (third Monday in January)
            return False

        if ((year <= 1968 or (year <= 1980 and year % 4 == 0)) and month == 11
                and day <= 7 and weekday == Weekday.Tuesday):
            # Presidential election days
            return False

        # Special closings
        if (  # President Bush's Funeral
                (year == 2018 and month == 12 and day == 5)
                # Hurricane Sandy
                or (year == 2012 and month == 10 and (day == 29 or day == 30))
                # President Ford's funeral
                or (year == 2007 and month == 1 and day == 2)
                # President Reagan's funeral
                or (year == 2004 and month == 6 and day == 11)
                # September 11-14, 2001
                or (year == 2001 and month == 9 and (11 <= day <= 14))
                # President Nixon's funeral
                or (year == 1994 and month == 4 and day == 27)
                # Hurricane Gloria
                or (year == 1985 and month == 9 and day == 27)
                # 1977 Blackout
                or (year == 1977 and month == 7 and day == 14)
                # Funeral of former President Lyndon B. Johnson.
                or (year == 1973 and month == 1 and day == 25)
                # Funeral of former President Harry S. Truman
                or (year == 1972 and month == 12 and day == 28)
                # National Day of Participation for the lunar exploration.
                or (year == 1969 and month == 7 and day == 21)
                # Funeral of former President Eisenhower.
                or (year == 1969 and month == 3 and day == 31)
                # Closed all day - heavy snow.
                or (year == 1969 and month == 2 and day == 10)
                # Day after Independence Day.
                or (year == 1968 and month == 7 and day == 5)
                # June 12-Dec. 31, 1968
                # Four day week (closed on Wednesdays) - Paperwork Crisis
                or (year == 1968 and day_of_year >= 163 and weekday == Weekday.Wednesday)
                # Day of mourning for Martin Luther King Jr.
                or (year == 1968 and month == 4 and day == 9)
                # Funeral of President Kennedy
                or (year == 1963 and month == 11 and day == 25)
                # Day before Decoration Day
                or (year == 1961 and month == 5 and day == 29)
                # Day after Christmas
                or (year == 1958 and month == 12 and day == 26)
                # Christmas Eve
                or ((year == 1954 or year == 1956 or year == 1965)
                    and month == 12 and day == 24)):
            return False
        return True

    def _is_business_day_us_government_bond(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        easter_monday = self.easter_monday(year=year,
                                           easter_monday_type=EasterMondayTypes.Western)
        if (self.is_weekend(weekday)
                # New Year's Day (possibly moved to Monday if on Sunday)
                or ((day == 1 or (day == 2 and weekday == Weekday.Monday)) and month == 1)
                # Martin Luther King's birthday (third Monday in January)
                or ((15 <= day <= 21) and weekday == Weekday.Monday and month == 1
                    and year >= 1983)
                # Washington's birthday (third Monday in February)
                or self.is_washington_birthday(year=year, month=month, weekday=weekday, day=day)
                # Good Friday (2015 was half day due to NFP report)
                or ((date == easter_monday - timedelta(days=3)) and year != 2015)
                # Memorial Day (last Monday in May)
                or self.is_memorial_day(year=year, month=month, weekday=weekday, day=day)
                # Juneteenth (Monday if Sunday or Friday if Saturday)
                or self.is_juneteenth(year=year, month=month, weekday=weekday, day=day)
                # Independence Day (Monday if Sunday or Friday if Saturday)
                or ((day == 4 or (day == 5 and weekday == Weekday.Monday) or
                     (day == 3 and weekday == Weekday.Friday)) and month == 7)
                # Labor Day (first Monday in September)
                or self.is_labor_day(month=month, weekday=weekday, day=day)
                # Columbus Day (second Monday in October)
                or self.is_columbus_day(year=year, month=month, weekday=weekday, day=day)
                # Veteran's Day (Monday if Sunday)
                or self.is_veterans_day_no_saturday(year=year, month=month, weekday=weekday, day=day)
                # Thanksgiving Day (fourth Thursday in November)
                or ((22 <= day <= 28) and weekday == Weekday.Thursday and month == 11)
                # Christmas (Monday if Sunday or Friday if Saturday)
                or ((day == 25 or (day == 26 and weekday == Weekday.Monday) or
                     (day == 24 and weekday == Weekday.Friday)) and month == 12)):
            return False

            # Special closings
        if (  # President Bush's Funeral
                (year == 2018 and month == 12 and day == 5)
                # Hurricane Sandy
                or (year == 2012 and month == 10 and (day == 30))
                # President Reagan's funeral
                or (year == 2004 and month == 6 and day == 11)):
            return False
        return True

    def _is_business_day_us_nerc(self, date: datetime) -> bool:
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        if (self.is_weekend(weekday)
                # New Year's Day (possibly moved to Monday if on Sunday)
                or ((day == 1 or (day == 2 and weekday == Weekday.Monday)) and month == 1)
                # Memorial Day (last Monday in May)
                or self.is_memorial_day(year=year, month=month, weekday=weekday, day=day)
                # Independence Day (Monday if Sunday)
                or ((day == 4 or (day == 5 and weekday == Weekday.Monday)) and month == 7)
                # Labor Day (first Monday in September)
                or self.is_labor_day(month=month, weekday=weekday, day=day)
                # Thanksgiving Day (fourth Thursday in November)
                or ((22 <= day <= 28) and weekday == Weekday.Thursday and month == 11)
                # Christmas (Monday if Sunday)
                or ((day == 25 or (day == 26 and weekday == Weekday.Monday)) and month == 12)):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True

    def _is_business_day_us_federal_reserve(self, date: datetime) -> bool:
        # see https://www.frbservices.org/holidayschedules/ for details
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        if (self.is_weekend(weekday)
                # New Year's Day (possibly moved to Monday if on Sunday)
                or ((day == 1 or (day == 2 and weekday == Weekday.Monday)) and month == 1)
                # Martin Luther King's birthday (third Monday in January)
                or ((15 <= day <= 21) and weekday == Weekday.Monday and month == 1
                    and year >= 1983)
                # Washington's birthday (third Monday in February)
                or self.is_washington_birthday(year=year, month=month, weekday=weekday, day=day)
                # Memorial Day (last Monday in May)
                or self.is_memorial_day(year=year, month=month, weekday=weekday, day=day)
                # Juneteenth (Monday if Sunday or Friday if Saturday)
                or self.is_juneteenth(year=year, month=month, weekday=weekday, day=day)
                # Independence Day (Monday if Sunday)
                or ((day == 4 or (day == 5 and weekday == Weekday.Monday)) and month == 7)
                # Labor Day (first Monday in September)
                or self.is_labor_day(month=month, weekday=weekday, day=day)
                # Columbus Day (second Monday in October)
                or self.is_columbus_day(year=year, month=month, weekday=weekday, day=day)
                # Veteran's Day (Monday if Sunday)
                or self.is_veterans_day_no_saturday(year=year, month=month, weekday=weekday, day=day)
                # Thanksgiving Day (fourth Thursday in November)
                or ((22 <= day <= 28) and weekday == Weekday.Thursday and month == 11)
                # Christmas (Monday if Sunday)
                or ((day == 25 or (day == 26 and weekday == Weekday.Monday)) and month == 12)):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True

    @staticmethod
    def is_washington_birthday(year: int,
                               month: int,
                               weekday: Weekday,
                               day: int) -> bool:
        """
        :param year:
        :param month:
        :param weekday:
        :param day:
        :return:
        """
        if year >= 1971:
            # third Monday in February
            return (15 <= day <= 21) and weekday == Weekday.Monday and month == 2
        else:
            # February 22nd, possily adjusted
            return (day == 22 or (day == 23 and weekday == Weekday.Monday) or (
                    day == 21 and weekday == Weekday.Friday)) and month == 2

    @staticmethod
    def is_memorial_day(year: int,
                        month: int,
                        weekday: Weekday,
                        day: int) -> bool:
        if year >= 1971:
            # last Monday in May
            return day >= 25 and weekday == Weekday.Monday and month == 5
        else:
            # May 30th, possibly adjusted
            return (day == 30 or (day == 31 and weekday == Weekday.Monday) or (
                    day == 29 and weekday == Weekday.Friday)) and month == 5

    @staticmethod
    def is_labor_day(month: int,
                     weekday: Weekday,
                     day: int) -> bool:
        # first Monday in September
        return day <= 7 and weekday == Weekday.Monday and month == 9

    @staticmethod
    def is_columbus_day(year: int,
                        month: int,
                        weekday: Weekday,
                        day: int) -> bool:
        # second Monday in October
        return (8 <= day <= 14) and weekday == Weekday.Monday and month == 10 and year >= 1971

    @staticmethod
    def is_veterans_day(year: int,
                        month: int,
                        weekday: Weekday,
                        day: int) -> bool:
        if year <= 1970 or year >= 1978:
            # November 11th, adjusted
            return (day == 11 or (day == 12 and weekday == Weekday.Monday) or (
                    day == 10 and weekday == Weekday.Friday)) and month == 11
        else:
            # fourth Monday in October
            return (22 <= day <= 28) and weekday == Weekday.Monday and month == 10

    @staticmethod
    def is_veterans_day_no_saturday(year: int,
                                    month: int,
                                    weekday: Weekday,
                                    day: int) -> bool:
        if year <= 1970 or year >= 1978:
            # November 11th, adjusted, but no Saturday to Friday
            return (day == 11 or (day == 12 and weekday == Weekday.Monday)) and month == 11
        else:
            # fourth Monday in October
            return (22 <= day <= 28) and weekday == Weekday.Monday and month == 10

    @staticmethod
    def is_juneteenth(year: int,
                      month: int,
                      weekday: Weekday,
                      day: int) -> bool:
        # declared in 2021, but only observed by exchanges since 2022
        return (day == 19 or (day == 20 and weekday == Weekday.Monday) or (
                day == 18 and weekday == Weekday.Friday)) and month == 6 and year >= 2022
