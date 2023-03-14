import sys

from qtmodel.error import qt_ensure
from qtmodel.quote import Quote
from qtmodel.types import Real


class SimpleQuote(Quote):
    """ market element returning a stored value """

    def __init__(self, value: Real = sys.float_info.max):
        super(SimpleQuote, self).__init__()
        self._value = value

    def value(self):
        qt_ensure(self.is_valid(), "invalid SimpleQuote")
        return self._value

    def is_valid(self):
        return self._value != sys.float_info.max

    def set_value(self, value: Real = None):
        diff = value - self._value
        if diff != 0.0:
            self._value = value
            self.notify_observers()

        return diff

    def reset(self):
        self.set_value(sys.float_info.max)
