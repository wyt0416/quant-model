from abc import ABCMeta, abstractmethod
from collections import defaultdict
from datetime import datetime

from qtmodel.error import qt_require, QTError
from qtmodel.patterns.lazyobject import LazyObject
from qtmodel.patterns.observable import Observable, Observer
from qtmodel.pricingengine import PricingEngineResults, PricingEngine, PricingEngineArguments
from qtmodel.types import Real


class InstrumentResults(PricingEngineResults):
    def __init__(self):
        self.value: Real = None
        self.error_estimate: Real = None
        self.valuation_date: datetime = None
        self.additional_results: dict = {}

    def reset(self):
        self.value = self.error_estimate = None
        self.valuation_date = None
        self.additional_results.clear()


class Instrument(LazyObject, Observable, Observer, metaclass=ABCMeta):
    """
    Abstract instrument class
    This class is purely abstract and defines the interface of concrete
    instruments which will be derived from this one.
    """

    def __init__(self):
        LazyObject.__init__(self)
        Observable.__init__(self)
        Observer.__init__(self)

        self._NPV: Real = None
        self._error_estimate: Real = None
        self._valuation_date: datetime = None
        self._additional_results: dict = defaultdict(lambda: None)
        self._engine: PricingEngine = None

    def calculate(self):
        if not self._calculated:
            if self.is_expired():
                self.setup_expired()
                self._calculated = True
            else:
                LazyObject.calculate(self)

    def NPV(self):
        """
        returns the net present value of the instrument.
        :return:
        """
        self.calculate()
        qt_require(self._NPV is not None, "NPV not provided")
        return self._NPV

    def error_estimate(self):
        """
        returns the error estimate on the NPV when available.
        :return:
        """
        self.calculate()
        qt_require(self._error_estimate is not None,
                   "error estimate not provided")
        return self._error_estimate

    def valuation_date(self):
        """
        returns the date the net present value refers to.
        :return:
        """
        self.calculate()
        qt_require(self._valuation_date is not None,
                   "valuation date not provided")
        return self._valuation_date

    def result(self, tag: str):
        """ returns any additional result returned by the pricing engine. """
        self.calculate()
        value = self._additional_results[tag]
        qt_require(value is not None, f"{tag} not provided")
        return value

    def additional_results(self):
        """ returns all additional result returned by the pricing engine. """
        self.calculate()
        return self._additional_results

    @abstractmethod
    def is_expired(self):
        """
        returns whether the instrument might have value greater than zero.
        :return:
        """
        pass

    def set_pricing_engine(self, e: PricingEngine):
        """ set the pricing engine to be used. """
        if self._engine is not None:
            self.unregister_with(self._engine)
        self._engine = e
        if self._engine is not None:
            self.register_with(self._engine)
        # trigger(lazy) recalculation and notify observers
        self.update()

    def setup_arguments(self, arguments: PricingEngineArguments):
        """
        When a derived argument structure is defined for an
        instrument, this method should be overridden to fill
        it. This is mandatory in case a pricing engine is used.
        :param arguments:
        :return:
        """
        raise QTError("setup_arguments() not implemented")

    def fetch_results(self, r: PricingEngineResults):
        """
        When a derived result structure is defined for an
        instrument, this method should be overridden to read from
        it. This is mandatory in case a pricing engine is used.
        :return:
        """
        self._NPV = r.value
        self._error_estimate = r.error_estimate
        self._valuation_date = r.valuation_date

        self._additional_results = r.additional_results

    def setup_expired(self):
        self._NPV = self._error_estimate = 0.0
        self._valuation_date = None
        self._additional_results.clear()

    def perform_calculations(self):
        """
        In case a pricing engine is not used, this
        method must be overridden to perform the actual
        calculations and set any needed results. In case
        a pricing engine is used, the default implementation
        can be used.
        :return:
        """
        qt_require(self._engine is not None, "null pricing engine")
        self._engine.reset()
        self.setup_arguments(self._engine.get_arguments())
        self._engine.get_arguments().validate()
        self._engine.calculate()
        self.fetch_results(self._engine.get_results())
