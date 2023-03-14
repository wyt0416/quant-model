from datetime import datetime
from enum import Enum
from typing import List

from qtmodel.error import QTError
from qtmodel.time.calendar import Calendar
from qtmodel.time.weekday import Weekday


class JointCalendarRule(Enum):
    """ rules for joining calendars """
    # A date is a holiday for the joint calendar if it
    # is a holiday for any of the given calendars
    JoinHolidays = "Join Holidays"
    # A date is a business day for the joint calendar if
    # it is a business day for any of the given calendars
    JoinBusinessDays = "Join Business Days"


class JointCalendar(Calendar):
    """
    Joint calendar
    Depending on the chosen rule, this calendar has a set of
    business days given by either the union or the intersection
    of the sets of business days of the given calendars.
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self,
                 calendars: List[Calendar],
                 joint_calendar_rule: JointCalendarRule = JointCalendarRule.JoinHolidays):
        self.calendars = calendars
        self.joint_calendar_rule = joint_calendar_rule

    def name(self) -> str:
        out_str = ""
        if self.joint_calendar_rule == JointCalendarRule.JoinHolidays:
            out_str += "JoinHolidays("
        elif self.joint_calendar_rule == JointCalendarRule.JoinBusinessDays:
            out_str += "JoinBusinessDays("
        else:
            raise QTError("unknown joint calendar rule")
        out_str += self.calendars[0].name()
        for calendar in self.calendars[1:]:
            out_str += f", {calendar.name()}"
        out_str += ")"
        return out_str

    def is_weekend(self, w: Weekday) -> bool:
        if self.joint_calendar_rule == JointCalendarRule.JoinHolidays:
            for calendar in self.calendars:
                if calendar.is_weekend(w=w):
                    return True
            return False
        elif self.joint_calendar_rule == JointCalendarRule.JoinBusinessDays:
            for calendar in self.calendars:
                if not calendar.is_weekend(w=w):
                    return False
            return True
        else:
            raise QTError("unknown joint calendar rule")

    def _is_business_day(self, date: datetime) -> bool:
        if self.joint_calendar_rule == JointCalendarRule.JoinHolidays:
            for calendar in self.calendars:
                if calendar.is_holiday(date=date):
                    return False
            return True
        elif self.joint_calendar_rule == JointCalendarRule.JoinBusinessDays:
            for calendar in self.calendars:
                if calendar.is_business_day(date=date):
                    return True
            return False
        else:
            raise QTError("unknown joint calendar rule")
