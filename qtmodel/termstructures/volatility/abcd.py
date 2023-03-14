import math

from qtmodel.error import qt_require
from qtmodel.math.abcdmathfunction import AbcdMathFunction
from qtmodel.math.comparison import close
from qtmodel.types import Real


class AbcdFunction(AbcdMathFunction):
    """ Abcd functional form for instantaneous volatility """

    def __init__(self,
                 a: Real = -0.06,
                 b: Real = 0.17,
                 c: Real = 0.54,
                 d: Real = 0.17):
        super().__init__(a, b, c, d)

    def maximum_volatility(self):
        """ maximum value of the volatility function """
        return self.maximum_value()

    def short_term_volatility(self):
        """ volatility function value at time 0 """
        return self(0.0)

    def long_term_volatility(self):
        """ volatility function value at time +inf """
        return self.long_term_value()

    def covariance(self,
                   t: Real,
                   T: Real,
                   S: Real,
                   t2: Real = None):
        """
        instantaneous covariance function at time t between T-fixing and S-fixing rates
        :param t:
        :param T:
        :param S:
        :return:
        """
        if t2 is None:
            return self(T - t) * self(S - t)
        else:
            qt_require(t <= t2,
                       f"integrations bounds ({t}, {t2}) are in reverse order")
            cut_off = min(S, T)
            if t >= cut_off:
                return 0.0
            else:
                cut_off = min(t2, cut_off)
                return self.primitive(cut_off, T, S) - self.primitive(t, T, S)

    def primitive(self,
                  t: Real,
                  T: Real,
                  S: Real):
        """
        indefinite integral of the instantaneous covariance function at
        time t between T-fixing and S-fixing rates
        :param t:
        :param T:
        :param S:
        :return:
        """
        if T < t or S < t:
            return 0.0

        if close(self._c, 0.0):
            v = self._a + self._d
            return t * (
                        v * v + v * self._b * S + v * self._b * T - v * self._b * t + self._b * self._b * S * T - 0.5 *
                        self._b * self._b * t * (
                            S + T) + self._b * self._b * t * t / 3.0)

        k1 = math.exp(self._c * t)
        k2 = math.exp(self._c * S)
        k3 = math.exp(self._c * T)

        return (self._b * self._b * (-1 - 2 * self._c * self._c * S * T - self._c * (S + T)
                                     + k1 * k1 * (1 + self._c * (S + T - 2 * t) + 2 * self._c * self._c * (S - t) * (
                        T - t)))
                + 2 * self._c * self._c * (2 * self._d * self._a * (k2 + k3) * (k1 - 1)
                                           + self._a * self._a * (
                                                   k1 * k1 - 1) + 2 * self._c * self._d * self._d * k2 * k3 * t)
                + 2 * self._b * self._c * (
                        self._a * (-1 - self._c * (S + T) + k1 * k1 * (1 + self._c * (S + T - 2 * t)))
                        - 2 * self._d * (k3 * (1 + self._c * S) + k2 * (1 + self._c * T)
                                         - k1 * k3 * (1 + self._c * (S - t))
                                         - k1 * k2 * (1 + self._c * (T - t)))
                )
                ) / (4 * self._c * self._c * self._c * k2 * k3)

    def volatility(self,
                   t_min: Real,
                   t_max: Real,
                   T: Real):
        """
        average volatility in [tMin,tMax] of T-fixing rate
        :param t_min:
        :param t_max:
        :param T:
        :return:
        """
        if t_max == t_min:
            return self.instantaneous_volatility(t_max, T)
        qt_require(t_max > t_min, "tMax must be > tMin")
        return math.sqrt(self.variance(t_min, t_max, T) / (t_max - t_min))

    def instantaneous_volatility(self,
                                 u: Real,
                                 T: Real):
        """
        instantaneous volatility at time t of the T-fixing rate
        :param u:
        :param T:
        :return:
        """
        return math.sqrt(self.instantaneous_variance(u, T))

    def instantaneous_variance(self,
                               u: Real,
                               T: Real):
        """
        instantaneous variance at time t of T-fixing rate
        :param u:
        :param T:
        :return:
        """
        return self.instantaneous_covariance(u, T, T)

    def instantaneous_covariance(self,
                                 u: Real,
                                 T: Real,
                                 S: Real):
        """
        instantaneous covariance at time t between T and S fixing rates
        :param u:
        :param T:
        :param S:
        :return:
        """
        return self(T - u) * self(S - u)

    def variance(self,
                 t_min: Real,
                 t_max: Real,
                 T: Real):
        """
        variance between tMin and tMax of T-fixing rate
        :param t_min:
        :param t_max:
        :param T:
        :return:
        """
        return self.covariance(t_min, t_max, T, T)


class AbcdSquared:
    """ Helper class used by unit tests """

    def __init__(self,
                 a: Real,
                 b: Real,
                 c: Real,
                 d: Real,
                 T: Real,
                 S: Real):
        self._abcd = AbcdFunction(a, b, c, d)
        self._T = T
        self._S = S

    def __call__(self, t: Real):
        return self._abcd.covariance(t, self._T, self._S)


def abcd_black_volatility(u: Real,
                          a: Real,
                          b: Real,
                          c: Real,
                          d: Real):
    model = AbcdFunction(a, b, c, d)
    return model.volatility(0., u, u)
