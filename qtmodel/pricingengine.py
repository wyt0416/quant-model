from abc import ABCMeta, abstractmethod

from qtmodel.patterns.observable import Observable, Observer


class PricingEngineArguments(metaclass=ABCMeta):

    @abstractmethod
    def validate(self):
        pass


class PricingEngineResults(metaclass=ABCMeta):

    @abstractmethod
    def reset(self):
        pass


class PricingEngine(Observable, metaclass=ABCMeta):
    """ interface for pricing engines """

    @abstractmethod
    def get_arguments(self) -> PricingEngineArguments:
        pass

    @abstractmethod
    def get_results(self) -> PricingEngineResults:
        pass

    @abstractmethod
    def reset(self):
        pass

    @abstractmethod
    def calculate(self):
        pass


class GenericEngine(PricingEngine, Observer):
    """
    template base class for option pricing engines
    Derived engines only need to implement
    the calculate() method.
    """

    def __init__(self, arguments_type, results_type):
        PricingEngine.__init__(self)
        Observer.__init__(self)
        self._arguments: arguments_type = arguments_type()
        self._results: results_type = results_type()

    def get_arguments(self) -> PricingEngineArguments:
        return self._arguments

    def get_results(self) -> PricingEngineResults:
        return self._results

    def reset(self):
        self._results.reset()

    def update(self):
        self.notify_observers()
