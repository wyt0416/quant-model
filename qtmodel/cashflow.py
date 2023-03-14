from abc import ABCMeta, abstractmethod
from datetime import datetime

from qtmodel.event import Event
from qtmodel.patterns.visitor import Visitor
from qtmodel.settings import Settings


class CashFlow(Event, metaclass=ABCMeta):
    """
    Base class for cash flows
    This class is purely virtual and acts as a base class for the
    actual cash flow implementations.
    """

    @abstractmethod
    def date(self):
        """ This is inherited from the event class """
        pass

    def has_occurred(self, ref_date: datetime = None, include_ref_date: bool = None):
        """ returns true if an event has already occurred before a date """
        # easy and quick handling of most cases
        if ref_date is not None:
            cf = self.date()
            if ref_date < cf:
                return False
            if cf < ref_date:
                return True

        if ref_date is None or ref_date == Settings().evaluation_date():
            # today's date; we override the bool with the one
            # specified in the settings (if any)
            include_today = Settings().include_todays_cash_flows
            if include_today:  # NOLINT(readability-implicit-bool-conversion)
                include_ref_date = include_today

        return super().has_occurred(d=ref_date, include_ref_date=include_ref_date)

    @abstractmethod
    def amount(self):
        """ returns the amount of the cash flow """
        pass

    def ex_coupon_date(self):
        """ returns the date that the cash flow trades ex_coupon """
        return None

    def trading_ex_coupon(self, ref_date: datetime = None):
        """ returns true if the cashflow is trading ex-coupon on the ref_date """
        ecd = self.ex_coupon_date()
        if ecd is None:
            return False

        ref = ref_date if ref_date is not None else Settings().evaluation_date()

        return ecd <= ref

    def accept(self, v: Visitor):
        v.visit(self)


def earlier_than(c1: CashFlow, c2: CashFlow):
    return c1.date() < c2.date()
