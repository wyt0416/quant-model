import math
from typing import Union

import numpy as np

from qtmodel.stochasticprocess import StochasticProcessDiscretization, StochasticProcess1DDiscretization, \
    StochasticProcess, StochasticProcess1D
from qtmodel.types import Real


class EulerDiscretization(StochasticProcessDiscretization, StochasticProcess1DDiscretization):
    """ Euler discretization for stochastic processes """

    @staticmethod
    def drift(process: Union[StochasticProcess, StochasticProcess1D],
              t0: Real,
              x0: Union[list, Real],
              dt: Real) -> Union[list, Real]:
        """
        如果process是StochasticProcess类型，则x0要传list，返回值为list；
        如果process是StochasticProcess1D类型，则x0要传Real，返回值为Real
        :param process:
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return process.drift(t0, x0) * dt

    @staticmethod
    def diffusion(process: Union[StochasticProcess, StochasticProcess1D],
                  t0: Real,
                  x0: Union[list, Real],
                  dt: Real) -> Union[np.ndarray, Real]:
        """
        如果process是StochasticProcess类型，则x0要传list，返回值为np.ndarray；
        如果process是StochasticProcess1D类型，则x0要传Real，返回值为Real
        :param process:
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        return process.diffusion(t0, x0) * math.sqrt(dt)

    @staticmethod
    def covariance(process: StochasticProcess,
                   t0: Real,
                   x0: list,
                   dt: Real) -> np.ndarray:
        """
        :param process:
        :param t0:
        :param x0:
        :param dt:
        :return:
        """
        sigma = process.diffusion(t0, x0)
        result = sigma * sigma.transpose() * dt
        return result

    @staticmethod
    def variance(process: StochasticProcess1D,
                 t0: Real,
                 x0: Real,
                 dt: Real) -> Real:
        sigma = process.diffusion(t0, x0)
        return sigma * sigma * dt
