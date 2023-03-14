from abc import ABCMeta, abstractmethod

from qtmodel.patterns.observable import Observable


class Quote(Observable, metaclass=ABCMeta):
    """ purely virtual base class for market observables """

    @abstractmethod
    def value(self):
        """ returns the current value """
        pass

    @abstractmethod
    def is_valid(self):
        """ returns true if the Quote holds a valid value """
        pass
