from datetime import datetime

from qtmodel.time.calendar import Calendar, CalendarTypes
from qtmodel.time.weekday import Weekday


class NullCalendar(Calendar):
    """
    Calendar for reproducing theoretical calculations.
    This calendar has no holidays. It ensures that dates at
    whole-month distances have the same day of month.
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self):
        super().__init__(calendar_type=CalendarTypes.NONE)

    @staticmethod
    def is_weekend(w: Weekday) -> bool:
        return False

    def _is_business_day(self, date: datetime) -> bool:
        return True
