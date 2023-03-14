from datetime import datetime

from qtmodel.time.calendar import Calendar
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday


class BespokeCalendar(Calendar):
    """
    Bespoke calendar
    This calendar has no predefined set of business days. Holidays
    and weekdays can be defined by means of the provided interface.
    Instances constructed by copying remain linked to the original
    one; adding a new holiday or weekday will affect all linked
    instances.
    """

    def __init__(self, name: str = ""):
        self._name = name
        self._weekend = set()
        self.added_holidays = set()
        self.removed_holidays = set()

    def name(self) -> str:
        return self._name

    def is_weekend(self, w: Weekday) -> bool:
        return w in self._weekend

    def _is_business_day(self, date: datetime) -> bool:
        return not self.is_weekend(DateTool.weekday(date))

    def add_weekend(self, w: Weekday):
        self._weekend.add(w)
