from datetime import datetime

from qtmodel.error import QTError
from qtmodel.time.calendar import Calendar, CalendarTypes
from qtmodel.time.date import DateTool


class WeekendsOnly(Calendar):
    """
    Weekend Calendar
    """
    added_holidays = set()
    removed_holidays = set()
    def __init__(self):
        super().__init__(calendar_type=CalendarTypes.WEEKEND)

    def _is_business_day(self, date: datetime) -> bool:
        weekday = DateTool.weekday(date=date)
        return not self.is_weekend(w=weekday)
