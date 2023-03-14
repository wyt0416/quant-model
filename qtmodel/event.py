from abc import ABCMeta, abstractmethod
from datetime import datetime

from qtmodel.patterns.observable import Observable
from qtmodel.patterns.visitor import Visitor
from qtmodel.settings import Settings


class Event(Observable, metaclass=ABCMeta):
    """
    Base class for event
    This class acts as a base class for the actual
    event implementations.
    """

    @abstractmethod
    def date(self):
        """ returns the date at which the event occurs """
        pass

    def has_occurred(self,
                     d: datetime = None,
                     include_ref_date: bool = None):
        """
        returns true if an event has already occurred before a date
        If include_ref_date is True, then an event has not occurred if its
        date is the same as the ref_date, i.e. this method returns False if
        the event date is the same as the ref_date.
        """
        ref_date = d if d is not None else Settings().evaluation_date
        include_ref_date_event = include_ref_date if include_ref_date else Settings().include_reference_date_events
        if include_ref_date_event:
            return self.date() < ref_date
        else:
            return self.date() <= ref_date

    def accept(self, v: Visitor):
        v.visit(self)


class SimpleEvent(Event):
    """
    used to create an Event instance.
    to be replaced with specific events as soon as we find out which.
    """

    def __init__(self, date: datetime):
        super(SimpleEvent, self).__init__()
        self._date = date

    def date(self):
        return self._date
