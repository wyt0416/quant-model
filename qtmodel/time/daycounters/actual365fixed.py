from datetime import datetime
from enum import Enum

from qtmodel.error import QTError
from qtmodel.time.daycounter import DayCounter


class Actual365FixedConventionTypes(Enum):
    Standard = "Actual/365 (Fixed)"
    Canadian = "Actual/365 (Fixed) Canadian Bond"
    NoLeap = "Actual/365 (No Leap)"


class Actual365Fixed(DayCounter):
    def __init__(self,
                 convention: Actual365FixedConventionTypes = Actual365FixedConventionTypes.Standard):
        self.convention = convention

    def name(self) -> str:
        return self.convention.value

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        convention = self.convention
        if convention == Actual365FixedConventionTypes.Standard:
            return super().day_count(date1=date1, date2=date2) / 365
        elif convention == Actual365FixedConventionTypes.Canadian:
            if date1 == date2:
                return 0.0
            if ref_period_start is None:
                raise QTError("invalid ref_period_start")
            if ref_period_end is None:
                raise QTError("invalid ref_period_end")
            days_count1 = super().day_count(date1=date1, date2=date2)
            days_count2 = super().day_count(date1=ref_period_start, date2=ref_period_end)
            months = round(12 * days_count2 / 365)
            if months == 0:
                raise QTError("invalid reference period for Act/365 Canadian must be longer than a month.")
            frequency = int(12 / months)
            if days_count1 < int(365 / frequency):
                return days_count1 / 365
            return 1 / frequency - (days_count2 - days_count1) / 365
        elif convention == Actual365FixedConventionTypes.NoLeap:
            return self.day_count(date1=date1, date2=date2) / 365.0
        else:
            return QTError("unknown Actual/365 (Fixed) convention")

    def day_count(self, date1: datetime, date2: datetime):
        convention = self.convention
        if convention == Actual365FixedConventionTypes.Standard:
            return super().day_count(date1=date1, date2=date2)
        elif convention == Actual365FixedConventionTypes.Canadian:
            return super().day_count(date1=date1, date2=date2)
        elif convention == Actual365FixedConventionTypes.NoLeap:
            month_offset = [
                0, 31, 59, 90, 120, 151,  # Jan - Jun
                181, 212, 243, 273, 304, 334  # Jun - Dec
            ]
            serial_date1 = date1.day + month_offset[date1.month - 1] + date1.year * 365
            serial_date2 = date2.day + month_offset[date2.month - 1] + date2.year * 365
            if date1.month == 2 and date1.day == 29:
                serial_date1 -= 1
            if date2.month == 2 and date2.day == 29:
                serial_date2 -= 1
            return serial_date2 - serial_date1
        else:
            return QTError("unknown Actual/365 (Fixed) convention")
