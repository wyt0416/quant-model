from abc import ABCMeta, abstractmethod
from datetime import datetime

import numpy as np

from qtmodel.error import QTError, qt_require
from qtmodel.patterns.observable import Observer, Observable
from qtmodel.types import Real


class StochasticProcessDiscretization(metaclass=ABCMeta):
    """ discretization of a stochastic process over a given time interval """

    @staticmethod
    @abstractmethod
    def drift(process,
              t0: Real,
              x0: list,
              dt: Real) -> list:
        """
        :param process: StochasticProcess
        :param t0: Real
        :param x0: list
        :param dt: Real
        :return: list
        """
        pass

    @staticmethod
    @abstractmethod
    def diffusion(process,
                  t0: Real,
                  x0: list,
                  dt: Real) -> np.ndarray:
        """
        :param process: StochasticProcess
        :param t0: Real
        :param x0: list
        :param dt: Real
        :return: np.ndarray
        """
        pass

    @staticmethod
    @abstractmethod
    def covariance(process,
                   t0: Real,
                   x0: list,
                   dt: Real) -> np.ndarray:
        """
        :param process: StochasticProcess
        :param t0: Real
        :param x0: list
        :param dt: Real
        :return: np.ndarray
        """
        pass


class StochasticProcess(Observer, Observable, metaclass=ABCMeta):
    """
    multi-dimensional stochastic process class.
    This class describes a stochastic process governed by
    """

    def __init__(self, disc: StochasticProcessDiscretization):
        Observer.__init__(self)
        Observable.__init__(self)
        self._discretization = disc

    @abstractmethod
    def size(self) -> int:
        """
        returns the number of dimensions of the stochastic process
        :return:
        """
        pass

    def factors(self) -> int:
        """
        returns the number of independent factors of the process
        :return:
        """
        return self.size()

    @abstractmethod
    def initial_values(self) -> list:
        """
        returns the initial values of the state variables
        :return:
        """
        pass

    @abstractmethod
    def drift(self,
              t: Real,
              x: list) -> list:
        """
        returns the drift part of the equation
        :param t:
        :param x:
        :return:
        """
        pass

    @abstractmethod
    def diffusion(self,
                  t: Real,
                  x: list) -> np.ndarray:
        """
        returns the diffusion part of the equation
        :param t:
        :param x:
        :return:
        """
        pass

    def expectation(self,
                    t0: Real,
                    x0: list,
                    dt: Real) -> list:
        """
        returns the expectation
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return self.apply(x0, self._discretization.drift(self, t0, x0, dt))

    def std_deviation(self,
                      t0: Real,
                      x0: list,
                      dt: Real) -> np.ndarray:
        return self._discretization.diffusion(self, t0, x0, dt)

    def covariance(self,
                   t0: Real,
                   x0: list,
                   dt: Real) -> np.ndarray:
        return self._discretization.covariance(self, t0, x0, dt)

    def evolve(self,
               t0: Real,
               x0: list,
               dt: Real,
               dw: list) -> list:
        return self.apply(self.expectation(t0, x0, dt), self.std_deviation(t0, x0, dt) * dw)

    def apply(self,
              x0: list,
              dx: list):
        return x0 + dx

    def time(self, d: datetime):
        QTError("date/time conversion not supported")

    def update(self):
        self.notify_observers()


class StochasticProcess1DDiscretization(metaclass=ABCMeta):
    """ discretization of a 1-D stochastic process """

    @staticmethod
    @abstractmethod
    def drift(process,
              t0: Real,
              x0: Real,
              dt: Real) -> Real:
        """
        :param process: StochasticProcess1D
        :param t0: Real
        :param x0: Real
        :param dt: Real
        :return: Real
        """
        pass

    @staticmethod
    @abstractmethod
    def diffusion(process,
                  t0: Real,
                  x0: Real,
                  dt: Real) -> Real:
        """
        :param process: StochasticProcess1D
        :param t0: Real
        :param x0: Real
        :param dt: Real
        :return: Real
        """
        pass

    @staticmethod
    @abstractmethod
    def variance(process,
                 t0: Real,
                 x0: Real,
                 dt: Real) -> Real:
        """
        :param process: StochasticProcess1D
        :param t0: Real
        :param x0: Real
        :param dt: Real
        :return: Real
        """
        pass


class StochasticProcess1D(StochasticProcess, metaclass=ABCMeta):
    """ 1-dimensional stochastic process """

    def __init__(self, disc: StochasticProcess1DDiscretization):
        super().__init__(disc)
        self._discretization = disc

    @abstractmethod
    def x0(self):
        """
        returns the initial value of the state variable
        :return:
        """
        pass

    @abstractmethod
    def drift(self, t: Real, x: Real):
        """
        returns the drift part of the equation
        :param t:
        :param x:
        :return:
        """
        pass

    @abstractmethod
    def diffusion(self, t: Real, x: Real):
        """
        returns the diffusion part of the equation
        :param t:
        :param x:
        :return:
        """
        pass

    def expectation(self, t0: Real, x0: Real, dt: Real):
        """
        returns the expectation
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return self.apply(x0, self._discretization.drift(self, t0, x0, dt))

    def std_deviation(self, t0: Real, x0: Real, dt: Real):
        """
        returns the standard deviation
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return self._discretization.diffusion(self, t0, x0, dt)

    def variance(self, t0: Real, x0: Real, dt: Real):
        """
        returns the variance
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return self._discretization.variance(self, t0, x0, dt)

    def evolve(self, t0: Real, x0: Real, dt: Real, dw: Real):
        """
        :param t0:
        :param x0:
        :param dt:
        :param dw:
        :return:
        """
        return self.apply(self.expectation(t0, x0, dt), self.std_deviation(t0, x0, dt) * dw)

    def apply(self, x0: Real, dx: Real):
        return x0 + dx

    # StochasticProcess interface implementation
    def size(self) -> int:
        return 1

    def initial_values(self) -> list:
        a = [self.x0()]
        return a

    def covariance(self, t0: Real, x0: list, dt: Real) -> np.ndarray:
        qt_require(len(x0) == 1, "1-D array required")
        m = np.full((1, 1), self.variance(t0, x0[0], dt))
        return m

    def _drift(self, t: Real, x: list) -> list:
        qt_require(len(x) == 1, "1-D array required")
        a = [self.drift(t, x[0])]
        return a

    def _diffusion(self, t: Real, x: list) -> np.ndarray:
        qt_require(len(x) == 1, "1-D array required")
        m = np.full((1, 1), self.diffusion(t, x[0]))
        return m

    def _expectation(self, t0: Real, x0: list, dt: Real) -> list:
        qt_require(len(x0) == 1, "1-D array required")
        a = [self.expectation(t0, x0[0], dt)]
        return a

    def _std_deviation(self, t0: Real, x0: list, dt: Real) -> np.ndarray:
        qt_require(len(x0) == 1, "1-D array required")
        m = np.full((1, 1), self.std_deviation(t0, x0[0], dt))
        return m

    def _evolve(self, t0: Real, x0: list, dt: Real, dw: list):
        qt_require(len(x0) == 1, "1-D array required")
        qt_require(len(dw) == 1, "1-D array required")
        a = [self.evolve(t0, x0[0], dt, dw[0])]
        return a

    def _apply(self, x0: list, dx: list):
        qt_require(len(x0) == 1, "1-D array required")
        qt_require(len(dx) == 1, "1-D array required")
        a = [self.apply(x0[0], dx[0])]
        return a
