from enum import Enum

from qtmodel.error import QTError


class Weekday(Enum):
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6
    Sunday = 7

    def long_weekday_holder(self):
        if self == Weekday.Monday:
            return "Monday"
        elif self == Weekday.Tuesday:
            return "Tuesday"
        elif self == Weekday.Wednesday:
            return "Wednesday"
        elif self == Weekday.Thursday:
            return "Thursday"
        elif self == Weekday.Friday:
            return "Friday"
        elif self == Weekday.Saturday:
            return "Saturday"
        elif self == Weekday.Sunday:
            return "Sunday"
        else:
            raise QTError("unknown weekday")

    def short_weekday_holder(self):
        if self == Weekday.Monday:
            return "Mon"
        elif self == Weekday.Tuesday:
            return "Tue"
        elif self == Weekday.Wednesday:
            return "Wed"
        elif self == Weekday.Thursday:
            return "Thu"
        elif self == Weekday.Friday:
            return "Fri"
        elif self == Weekday.Saturday:
            return "Sat"
        elif self == Weekday.Sunday:
            return "Sun"
        else:
            raise QTError("unknown weekday")

    def shortest_weekday_holder(self):
        if self == Weekday.Monday:
            return "Mo"
        elif self == Weekday.Tuesday:
            return "Tu"
        elif self == Weekday.Wednesday:
            return "We"
        elif self == Weekday.Thursday:
            return "Th"
        elif self == Weekday.Friday:
            return "Fr"
        elif self == Weekday.Saturday:
            return "Sa"
        elif self == Weekday.Sunday:
            return "Su"
        else:
            raise QTError("unknown weekday")
