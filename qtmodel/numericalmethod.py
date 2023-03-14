from abc import ABCMeta, abstractmethod

from qtmodel.timegrid import TimeGrid
from qtmodel.types import Real


class Lattice(metaclass=ABCMeta):
    """ Lattice (tree, finite-differences) base class """

    def __init__(self, time_grid: TimeGrid):
        self._t = time_grid

    def time_grid(self):
        return self._t

    @abstractmethod
    def initialize(self, discretized_asset, time: Real):
        """
        initialize an asset at the given time.
        :param discretized_asset: DiscretizedAsset
        :param time:
        :return:
        """
        pass

    @abstractmethod
    def rollback(self, discretized_asset, to: Real):
        """
        Roll back an asset until the given time, performing any
        needed adjustment.
        :param discretized_asset: DiscretizedAsset
        :param to:
        :return:
        """
        pass

    @abstractmethod
    def partial_rollback(self, discretized_asset, to: Real):
        """
        Roll back an asset until the given time, but do not perform
        the final adjustment.
        :param discretized_asset: DiscretizedAsset
        :param to:
        :return:
        """
        pass

    @abstractmethod
    def present_value(self, discretized_asset):
        """
        computes the present value of an asset.
        :param discretized_asset: DiscretizedAsset
        :return:
        """
        pass

    @abstractmethod
    def grid(self, time: Real):
        """
        this is a smell, but we need it. We'll rethink it later.
        :param time:
        :return:
        """
        pass
