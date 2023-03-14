from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

from qtmodel.cashflow import CashFlow
from qtmodel.error import qt_require
from qtmodel.types import Real


class Dividend(CashFlow, metaclass=ABCMeta):
    """
    Predetermined cash flow
    This cash flow pays a predetermined amount at a given date.
    """

    def __init__(self, date: datetime):
        super(Dividend, self).__init__()
        self._date = date

    def date(self):
        return self._date

    @abstractmethod
    def amount(self, underlying: Real = None):
        pass


class FixedDividend(Dividend):
    """
    Predetermined cash flow
    This cash flow pays a predetermined amount at a given date.
    """

    def __init__(self, amount: Real, date: datetime):
        super(FixedDividend, self).__init__(date=date)
        self._amount = amount

    def amount(self, underlying: Real = None):
        return self._amount


class FractionalDividend(Dividend):
    """
    Predetermined cash flow
    This cash flow pays a fractional amount at a given date.
    """

    def __init__(self, rate: Real, date: datetime, nominal: Real = None):
        super(FractionalDividend, self).__init__(date=date)
        self._rate = rate
        self._nominal = nominal

    def amount(self, underlying: Real = None):
        if underlying is None:
            qt_require(self._nominal is not None, "no nominal given")
            return self._rate * self._nominal
        else:
            return self._rate * underlying


def dividend_vector(dividend_dates: List[datetime], dividends: List[Real]):
    qt_require(len(dividend_dates) == len(dividends),
               "size mismatch between dividend dates and amounts")
    items = []
    for d, dd in zip(dividends, dividend_dates):
        items.append(FixedDividend(d, dd))

    return items
