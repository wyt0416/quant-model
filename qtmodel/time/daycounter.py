from abc import ABCMeta, abstractmethod
from datetime import datetime
from enum import Enum


class DayCounterTypes(Enum):
    Actual360 = "Actual/360"
    Actual364 = "Actual/364"
    Actual365Fixed = "Actual/365(Fixed)"
    ActualActual = "Actual/Actual"
    Business252 = "Business/252"
    One = "1/1"
    Simple = "Simple"
    Thirty360 = "30/360"
    Thirty365 = "30/365"


class DayCounter(metaclass=ABCMeta):

    @abstractmethod
    def name(self):
        pass

    def day_count(self, date1: datetime, date2: datetime):
        """
        :param date1:
        :param date2:
        :return:
        """
        return (date2 - date1).days

    @staticmethod
    @abstractmethod
    def year_fraction(date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        """
        :param date1:
        :param date2:
        :param ref_period_start:
        :param ref_period_end:
        """
        pass

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
