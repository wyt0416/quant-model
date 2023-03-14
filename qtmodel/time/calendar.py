from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from enum import Enum

from qtmodel.error import QTError, qt_require
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.date import DateTool
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.weekday import Weekday


class CalendarTypes(Enum):
    WEEKEND = "Weekends only"
    TARGET = "TARGET"
    CHINA_SSE = "Shanghai stock exchange"
    CHINA_IB = "China inter bank market"
    UNITED_STATES_SETTLEMENT = "US settlement"
    UNITED_STATES_NYSE = "New York stock exchange"
    UNITED_STATES_GOVERNMENT_BOND = "US government bond market"
    UNITED_STATES_NERC = "North American Energy Reliability Council"
    UNITED_STATES_LIBOR_IMPACT = "US with Libor impact"
    UNITED_STATES_FEDERAL_RESERVE = "Federal Reserve Bankwire System"
    BRAZIL_SETTLEMENT = "Brazil"
    BRAZIL_EXCHANGE = "BOVESPA"
    JAPAN = "Japan"
    CANADA_SETTLEMENT = "Canada"
    CANADA_TSX = "TSX"
    NONE = "None"


class EasterMondayTypes(Enum):
    Western = "Western"
    Orthodox = "Orthodox"


western_easter_monday = [
    98, 90, 103, 95, 114, 106, 91, 111, 102,  # 1901-1909
    87, 107, 99, 83, 103, 95, 115, 99, 91, 111,  # 1910-1919
    96, 87, 107, 92, 112, 103, 95, 108, 100, 91,  # 1920-1929
    111, 96, 88, 107, 92, 112, 104, 88, 108, 100,  # 1930-1939
    85, 104, 96, 116, 101, 92, 112, 97, 89, 108,  # 1940-1949
    100, 85, 105, 96, 109, 101, 93, 112, 97, 89,  # 1950-1959
    109, 93, 113, 105, 90, 109, 101, 86, 106, 97,  # 1960-1969
    89, 102, 94, 113, 105, 90, 110, 101, 86, 106,  # 1970-1979
    98, 110, 102, 94, 114, 98, 90, 110, 95, 86,  # 1980-1989
    106, 91, 111, 102, 94, 107, 99, 90, 103, 95,  # 1990-1999
    115, 106, 91, 111, 103, 87, 107, 99, 84, 103,  # 2000-2009
    95, 115, 100, 91, 111, 96, 88, 107, 92, 112,  # 2010-2019
    104, 95, 108, 100, 92, 111, 96, 88, 108, 92,  # 2020-2029
    112, 104, 89, 108, 100, 85, 105, 96, 116, 101,  # 2030-2039
    93, 112, 97, 89, 109, 100, 85, 105, 97, 109,  # 2040-2049
    101, 93, 113, 97, 89, 109, 94, 113, 105, 90,  # 2050-2059
    110, 101, 86, 106, 98, 89, 102, 94, 114, 105,  # 2060-2069
    90, 110, 102, 86, 106, 98, 111, 102, 94, 114,  # 2070-2079
    99, 90, 110, 95, 87, 106, 91, 111, 103, 94,  # 2080-2089
    107, 99, 91, 103, 95, 115, 107, 91, 111, 103,  # 2090-2099
    88, 108, 100, 85, 105, 96, 109, 101, 93, 112,  # 2100-2109
    97, 89, 109, 93, 113, 105, 90, 109, 101, 86,  # 2110-2119
    106, 97, 89, 102, 94, 113, 105, 90, 110, 101,  # 2120-2129
    86, 106, 98, 110, 102, 94, 114, 98, 90, 110,  # 2130-2139
    95, 86, 106, 91, 111, 102, 94, 107, 99, 90,  # 2140-2149
    103, 95, 115, 106, 91, 111, 103, 87, 107, 99,  # 2150-2159
    84, 103, 95, 115, 100, 91, 111, 96, 88, 107,  # 2160-2169
    92, 112, 104, 95, 108, 100, 92, 111, 96, 88,  # 2170-2179
    108, 92, 112, 104, 89, 108, 100, 85, 105, 96,  # 2180-2189
    116, 101, 93, 112, 97, 89, 109, 100, 85, 105  # 2190-2199
]

orthodox_easter_monday = [
    105, 118, 110, 102, 121, 106, 126, 118, 102,  # 1901-1909
    122, 114, 99, 118, 110, 95, 115, 106, 126, 111,  # 1910-1919
    103, 122, 107, 99, 119, 110, 123, 115, 107, 126,  # 1920-1929
    111, 103, 123, 107, 99, 119, 104, 123, 115, 100,  # 1930-1939
    120, 111, 96, 116, 108, 127, 112, 104, 124, 115,  # 1940-1949
    100, 120, 112, 96, 116, 108, 128, 112, 104, 124,  # 1950-1959
    109, 100, 120, 105, 125, 116, 101, 121, 113, 104,  # 1960-1969
    117, 109, 101, 120, 105, 125, 117, 101, 121, 113,  # 1970-1979
    98, 117, 109, 129, 114, 105, 125, 110, 102, 121,  # 1980-1989
    106, 98, 118, 109, 122, 114, 106, 118, 110, 102,  # 1990-1999
    122, 106, 126, 118, 103, 122, 114, 99, 119, 110,  # 2000-2009
    95, 115, 107, 126, 111, 103, 123, 107, 99, 119,  # 2010-2019
    111, 123, 115, 107, 127, 111, 103, 123, 108, 99,  # 2020-2029
    119, 104, 124, 115, 100, 120, 112, 96, 116, 108,  # 2030-2039
    128, 112, 104, 124, 116, 100, 120, 112, 97, 116,  # 2040-2049
    108, 128, 113, 104, 124, 109, 101, 120, 105, 125,  # 2050-2059
    117, 101, 121, 113, 105, 117, 109, 101, 121, 105,  # 2060-2069
    125, 110, 102, 121, 113, 98, 118, 109, 129, 114,  # 2070-2079
    106, 125, 110, 102, 122, 106, 98, 118, 110, 122,  # 2080-2089
    114, 99, 119, 110, 102, 115, 107, 126, 118, 103,  # 2090-2099
    123, 115, 100, 120, 112, 96, 116, 108, 128, 112,  # 2100-2109
    104, 124, 109, 100, 120, 105, 125, 116, 108, 121,  # 2110-2119
    113, 104, 124, 109, 101, 120, 105, 125, 117, 101,  # 2120-2129
    121, 113, 98, 117, 109, 129, 114, 105, 125, 110,  # 2130-2139
    102, 121, 113, 98, 118, 109, 129, 114, 106, 125,  # 2140-2149
    110, 102, 122, 106, 126, 118, 103, 122, 114, 99,  # 2150-2159
    119, 110, 102, 115, 107, 126, 111, 103, 123, 114,  # 2160-2169
    99, 119, 111, 130, 115, 107, 127, 111, 103, 123,  # 2170-2179
    108, 99, 119, 104, 124, 115, 100, 120, 112, 103,  # 2180-2189
    116, 108, 128, 119, 104, 124, 116, 100, 120, 112  # 2190-2199
]


class Calendar(metaclass=ABCMeta):

    def __init__(self, calendar_type: CalendarTypes):
        self.calendar_type = calendar_type

    def add_holiday(self, date: datetime):
        # if date was a genuine holiday previously removed, revert the change
        self.removed_holidays.discard(date)
        # if it's already a holiday, leave the calendar alone.
        # Otherwise, add it.
        if self.is_business_day(date=date):
            self.added_holidays.add(date)

    def remove_holiday(self, date: datetime):
        # if d was an artificially-added holiday, revert the change
        self.added_holidays.discard(date)
        # if it's already a business day, leave the calendar alone.
        # Otherwise, add it.
        if not self.is_business_day(date=date):
            self.removed_holidays.add(date)

    def name(self) -> str:
        return self.calendar_type.value

    def is_business_day(self, date: datetime) -> bool:
        """
        :param date:
        :return:
        """
        if date in self.added_holidays:
            return False
        if date in self.removed_holidays:
            return True
        return self._is_business_day(date=date)

    @abstractmethod
    def _is_business_day(self, date: datetime) -> bool:
        pass

    def is_holiday(self, date: datetime) -> bool:
        return not self.is_business_day(date=date)

    @staticmethod
    def is_weekend(w: Weekday) -> bool:
        return w == Weekday.Saturday or w == Weekday.Sunday

    def is_end_of_month(self, date: datetime) -> bool:
        return date.month != self.adjust(date=date + timedelta(days=1)).month

    def end_of_month(self, date: datetime) -> datetime:
        this_month_end = DateTool.end_of_month(date=date)
        return self.adjust(date=this_month_end, convention=BusinessDayConvention.Preceding)

    def holiday_list(self,
                     begin: datetime,
                     end: datetime,
                     include_weekends: bool = False):
        qt_require(end >= begin, f"'begin' date ({begin}) must be equal to or earlier than 'end' date ({end})")
        result = []
        date = begin
        one_day = timedelta(days=1)
        while date <= end:
            w = DateTool.weekday(date=date)
            if self.is_holiday(date=date) and (include_weekends or not self.is_weekend(w=w)):
                result.append(date)
            date += one_day
        return result

    def business_day_list(self,
                          begin: datetime,
                          end: datetime):
        qt_require(end >= begin, f"'begin' date ({begin}) must be equal to or earlier than 'end' date ({end})")
        result = []
        date = begin
        one_day = timedelta(days=1)
        while date <= end:
            if self.is_business_day(date=date):
                result.append(date)
            date += one_day
        return result

    def adjust(self,
               date: datetime,
               convention: BusinessDayConvention = BusinessDayConvention.Following):
        if convention == BusinessDayConvention.Unadjusted:
            return date
        date1 = date
        one_day = timedelta(days=1)
        if convention == BusinessDayConvention.Following or \
                convention == BusinessDayConvention.Modified_Following or \
                convention == BusinessDayConvention.Half_Month_Modified_Following:
            while self.is_holiday(date1):
                date1 += one_day
            if convention == BusinessDayConvention.Modified_Following or \
                    convention == BusinessDayConvention.Half_Month_Modified_Following:
                if date1.month != date.month:
                    return self.adjust(date=date, convention=BusinessDayConvention.Preceding)
                if convention == BusinessDayConvention.Half_Month_Modified_Following:
                    if date.day <= 15 < date1.day:
                        return self.adjust(date=date, convention=BusinessDayConvention.Preceding)
        elif convention == BusinessDayConvention.Preceding or \
                convention == BusinessDayConvention.Modified_Preceding:
            while self.is_holiday(date1):
                date1 -= one_day
            if convention == BusinessDayConvention.Modified_Preceding and \
                    date1.month != date.month:
                return self.adjust(date=date, convention=BusinessDayConvention.Following)
        elif convention == BusinessDayConvention.Nearest:
            date2 = date
            while self.is_holiday(date1) and self.is_holiday(date2):
                date1 += one_day
                date2 -= one_day
            if self.is_holiday(date1):
                return date2
            else:
                return date1
        else:
            raise QTError("unknown business-day convention.")
        return date1

    def advance(self,
                date: datetime,
                n: int = None,
                unit: TimeUnit = None,
                convention: BusinessDayConvention = BusinessDayConvention.Following,
                end_of_month: bool = False,
                period: Period = None):
        """
        Advances the given date of the given number of business days and
        returns the result.
        note The input date is not modified.
        N and units should be inputted simultaneously, while f need to be inputted instead if n and units are missing.
        """
        if n is not None and unit is not None:
            if n == 0:
                return self.adjust(date=date, convention=convention)
            elif unit == TimeUnit.Days:
                date1 = date
                one_day = timedelta(days=1)
                if n > 0:
                    while n > 0:
                        date1 += one_day
                        while self.is_holiday(date1):
                            date1 += one_day
                        n -= 1
                else:
                    while n < 0:
                        date1 -= one_day
                        while self.is_holiday(date1):
                            date1 -= one_day
                        n += 1
                return date1
            elif unit == TimeUnit.Weeks:
                date1 = DateTool.advance(date=date, n=n, units=unit)
                return self.adjust(date=date1, convention=convention)
            else:
                date1 = DateTool.advance(date=date, n=n, units=unit)
                if end_of_month and self.is_end_of_month(date):
                    return self.end_of_month(date1)
                return self.adjust(date=date1, convention=convention)
        elif period is not None:
            return self.advance(date=date,
                                n=period.length,
                                unit=period.units,
                                convention=convention,
                                end_of_month=end_of_month)
        else:
            raise QTError("n and units must be passed together. If n and units are not passed, period must be passed")

    def business_days_between(self,
                              begin: datetime,
                              end: datetime,
                              include_begin: bool = True,
                              include_end: bool = False):
        num = 0
        one_day = timedelta(days=1)
        if begin != end:
            if begin < end:
                # the last one is treated separately to avoid
                # incrementing max_date()
                date = begin
                while date < end:
                    if self.is_business_day(date=date):
                        num += 1
                    date += one_day
                if self.is_business_day(date=end):
                    num += 1
            elif begin > end:
                date = end
                while date < begin:
                    if self.is_business_day(date=date):
                        num += 1
                    date += one_day
                if self.is_business_day(date=begin):
                    num += 1

            if self.is_business_day(begin) and not include_begin:
                num -= 1
            if self.is_business_day(end) and not include_end:
                num -= 1

            if begin > end:
                num = -num
        elif include_begin and include_end and self.is_business_day(date=begin):
            num = 1

        return num

    @staticmethod
    def easter_monday(year: int, easter_monday_type: EasterMondayTypes):
        """
        :return: datetime
        """

        def compute_em(easter_monday_list):
            """
            :param easter_monday_list:
            :return:
            """
            em_day = easter_monday_list[year - 1901]
            start_date = datetime(year, 1, 1)
            em = start_date + timedelta(days=em_day - 1)
            return em

        if easter_monday_type == EasterMondayTypes.Western:
            return compute_em(easter_monday_list=western_easter_monday)
        elif easter_monday_type == EasterMondayTypes.Orthodox:
            return compute_em(easter_monday_list=orthodox_easter_monday)
        else:
            raise QTError("unknown easter monday type.")

    def __eq__(self, other):
        """
        self==other.
        :param other: Calendar
        :return: bool
        """
        return self.name() == other.name()

    def __ne__(self, other):
        """
        self!=other.
        :param other: Calendar
        :return: bool
        """
        return not (self == other)
