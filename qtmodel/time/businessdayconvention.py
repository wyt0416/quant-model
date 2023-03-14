from enum import Enum


class BusinessDayConvention(Enum):
    """ These conventions specify the algorithm used to adjust a date in case
    it is not a valid business day. """
    # ISDA
    # Choose the first business day after the given holiday.
    Following = 1
    # Choose the first business day after the given holiday
    # unless it belongs to a different month, in which case
    # choose the first business day before the holiday.
    Modified_Following = 2
    # Choose the first business day before the given holiday.
    Preceding = 3
    # NON ISDA
    # Choose the first business day before the given holiday
    # unless it belongs to a different month, in which case
    # choose the first business day after the holiday.
    Modified_Preceding = 4
    # Do not adjust.
    Unadjusted = 5
    # Choose the first business day after the given holiday
    # unless that day crosses the mid-month (15th) or the end
    # of month, in which case choose the first business day
    # before the holiday.
    Half_Month_Modified_Following = 6
    # Choose the nearest business day to the given holiday.
    # If both the preceding and following business days are
    # equally far away, default to following business day.
    Nearest = 7
