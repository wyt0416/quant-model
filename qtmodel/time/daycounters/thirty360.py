import calendar
from datetime import datetime
from enum import Enum

from qtmodel.error import QTError
from qtmodel.time.daycounter import DayCounter


class Thirty360ConventionTypes(Enum):
    USA = "30/360 (US)"
    BondBasis = "30/360 (Bond Basis)"
    European = "30E/360 (European)"
    EurobondBasis = "30E/360 (Eurobond Basis)"
    Italian = "30/360 (Italian)"
    German = "30E/360 (German)"
    ISMA = "30E/360 (ISMA)"
    ISDA = "30E/360 (ISDA)"
    NASD = "30/360 (NASD)"


class Thirty360(DayCounter):
    def __init__(self,
                 convention: Thirty360ConventionTypes = Thirty360ConventionTypes.BondBasis,
                 termination_date: datetime = None,
                 is_last_period: bool = False):
        self.convention = convention
        self.termination_date = termination_date
        self.is_last_period = is_last_period

    def name(self):
        return self.convention.value

    def day_count(self, date1: datetime, date2: datetime):
        if self.convention == Thirty360ConventionTypes.USA:
            return self.day_count_us(date1, date2)
        elif self.convention == Thirty360ConventionTypes.European or \
                self.convention == Thirty360ConventionTypes.EurobondBasis:
            return self.day_count_eu(date1, date2)
        elif self.convention == Thirty360ConventionTypes.Italian:
            return self.day_count_it(date1, date2)
        elif self.convention == Thirty360ConventionTypes.ISMA or \
                self.convention == Thirty360ConventionTypes.BondBasis:
            return self.day_count_isma(date1, date2)
        elif self.convention == Thirty360ConventionTypes.ISDA or \
                self.convention == Thirty360ConventionTypes.German:
            return self.day_count_isda(date1, date2)
        elif self.convention == Thirty360ConventionTypes.NASD:
            return self.day_count_nasd(date1, date2)
        else:
            raise QTError("unknown 30/360 convention")

    def day_count_us(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31 and day1 >= 30:
            day2 = 30

        if self.is_last_of_february(year2, month2, day2) and self.is_last_of_february(year1, month1, day1):
            day2 = 30
        if self.is_last_of_february(year1, month1, day1):
            day1 = 30

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def day_count_isma(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31 and day1 == 30:
            day2 = 30

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def day_count_eu(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31:
            day2 = 30

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def day_count_it(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31:
            day2 = 30

        if month1 == 2 and day1 > 27:
            day1 = 30
        if month2 == 2 and day2 > 27:
            day2 = 30

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def day_count_isda(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31:
            day2 = 30

        if self.is_last_of_february(year1, month1, day1):
            day1 = 30

        is_termination_date = self.is_last_period if self.termination_date is None else date2 == self.termination_date
        if not is_termination_date and self.is_last_of_february(year2, month2, day2):
            day2 = 30

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def day_count_nasd(self, date1: datetime, date2: datetime):
        day1 = date1.day
        day2 = date2.day
        month1 = date1.month
        month2 = date2.month
        year1 = date1.year
        year2 = date2.year

        if day1 == 31:
            day1 = 30
        if day2 == 31 and day1 >= 30:
            day2 = 30
        if day2 == 31 and day1 < 30:
            day2 = 1
            month2 += 1

        return 360 * (year2 - year1) + 30 * (month2 - month1) + (day2 - day1)

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        return self.day_count(date1=date1, date2=date2) / 360.0

    @staticmethod
    def is_last_of_february(year: int,
                            month: int,
                            day: int):
        return month == 2 and day == 28 + (1 if calendar.isleap(year) else 0)
