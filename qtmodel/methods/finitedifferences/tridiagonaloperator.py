from abc import ABCMeta, abstractmethod

from qtmodel.error import QTError, qt_require, qt_ensure
from qtmodel.math.comparison import close
from qtmodel.types import Real


class TimeSetter(metaclass=ABCMeta):
    """ encapsulation of time-setting logic """

    @staticmethod
    @abstractmethod
    def set_time(t: Real, L):
        """
        :param t:
        :param L: TridiagonalOperator
        :return:
        """
        pass


class TridiagonalOperator:
    """ Base implementation for tridiagonal operator """

    def __init__(self,
                 low: list = None,
                 mid: list = None,
                 high: list = None,
                 size: int = 0,
                 from_=None):
        self._time_setter: TimeSetter = None
        if low is None and mid is None and high is None and from_ is None:
            if size >= 2:
                self._n = size
                self._diagonal = [None] * size
                self._lower_diagonal = [None] * (size - 1)
                self._upper_diagonal = [None] * (size - 1)
                self._temp = [None] * size
            elif size == 0:
                self._n = 0
                self._diagonal = None
                self._lower_diagonal = None
                self._upper_diagonal = None
                self._temp = None
            else:
                QTError(f"invalid size ({size}) for tridiagonal operator (must be 0 or >= 2)")
        elif low is not None and mid is not None and high is not None and from_ is None:
            self._n = len(mid)
            self._diagonal = mid
            self._lower_diagonal = low
            self._upper_diagonal = high
            self._temp = [None] * self._n
            qt_require(len(low) == self._n - 1,
                       f"low diagonal vector of size {len(low)} instead of {self._n - 1}")
            qt_require(len(high) == self._n - 1,
                       f"high diagonal vector of size {len(high)} instead of {self._n - 1}")
        elif from_ is not None:
            self.swap(from_)
        else:
            raise QTError("it's not in the three scenarios")

    def swap(self, from_, to_=None):
        if to_ is None:
            self._n, from_._n = from_._n, self._n
            self._diagonal, from_._diagonal = from_._diagonal, self._diagonal
            self._lower_diagonal, from_._lower_diagonal = from_._lower_diagonal, self._lower_diagonal
            self._upper_diagonal, from_._upper_diagonal = from_._upper_diagonal, self._upper_diagonal
            self._temp, from_._temp = from_._temp, self._temp
            self._time_setter, from_._time_setter = from_._time_setter, self._time_setter
        else:
            from_.swap(to_)

    def apply_to(self, v: list):
        """ apply operator to a given array """
        qt_require(self._n != 0,
                   "uninitialized TridiagonalOperator")
        qt_require(len(v) == self._n,
                   f"vector of the wrong size {len(v)} instead of {self._n}")
        result = list(map(lambda a, b: a * b, self._diagonal, v))

        # matricial product
        result[0] += self._upper_diagonal[0] * v[1]
        for j in range(1, self._n - 1):
            result[j] += self._lower_diagonal[j - 1] * v[j - 1] + self._upper_diagonal[j] * v[j + 1]
        result[self._n - 1] += self._lower_diagonal[self._n - 2] * v[self._n - 2]

        return result

    def solve_for(self, rhs: list, result: list = None):
        """ solve linear system for a given right-hand side """
        if result is None:
            result = [None] * len(rhs)
            self.solve_for(rhs, result)
            return result
        else:
            qt_require(self._n != 0,
                       "uninitialized TridiagonalOperator")
            qt_require(len(rhs) == self._n,
                       f"rhs vector of size {len(rhs)} instead of {self._n}")

            bet = self._diagonal[0]
            qt_require(not close(bet, 0.0),
                       f"diagonal's first element ({bet}) cannot be close to zero")
            result[0] = rhs[0] / bet
            for j in range(1, self._n):
                self._temp[j] = self._upper_diagonal[j - 1] / bet
                bet = self._diagonal[j] - self._lower_diagonal[j - 1] * self._temp[j]
                qt_ensure(not close(bet, 0.0), "division by zero")
                result[j] = (rhs[j] - self._lower_diagonal[j - 1] * result[j - 1]) / bet

            # cannot be j>=0 with Size j
            for j in range(self._n - 2, 0, -1):
                result[j] -= self._temp[j + 1] * result[j + 1]
            result[0] -= self._temp[1] * result[1]

    def SOR(self, rhs: list, tol: Real):
        """ solve linear system with SOR approach """
        qt_require(self._n != 0,
                   "uninitialized TridiagonalOperator")
        qt_require(len(rhs) == self._n,
                   f"rhs vector of size {len(rhs)} instead of {self._n}")

        # initial guess
        result = rhs

        # solve tridiagonal system with SOR technique
        omega = 1.5
        err = 2.0 * tol
        for sor_iteration in range(tol):
            qt_require(sor_iteration < 100000,
                       f"tolerance ({tol}) not reached in {sor_iteration} iterations. The error still is {err}")

            temp = omega * (rhs[0] -
                            self._upper_diagonal[0] * result[1] -
                            self._diagonal[0] * result[0]) / self._diagonal[0]
            err = temp * temp
            result[0] += temp
            i = None
            for i in range(1, self._n - 1):
                temp = omega * (rhs[i] -
                                self._upper_diagonal[i] * result[i + 1] -
                                self._diagonal[i] * result[i] -
                                self._lower_diagonal[i - 1] * result[i - 1]) / self._diagonal[i]
                err += temp * temp
                result[i] += temp

            temp = omega * (rhs[i] -
                            self._diagonal[i] * result[i] -
                            self._lower_diagonal[i - 1] * result[i - 1]) / self._diagonal[i]
            err += temp * temp
            result[i] += temp
        return result

    @staticmethod
    def identity(size: int):
        """ identity instance """
        return TridiagonalOperator(low=[0.0] * (size - 1),  # lower diagonal
                                   mid=[1.0] * size,  # diagonal
                                   high=[0.0] * (size - 1))  # upper diagonal

    def size(self):
        return self._n

    def is_time_dependent(self):
        return not not self._time_setter

    def lower_diagonal(self):
        return self._lower_diagonal

    def diagonal(self):
        return self._diagonal

    def upper_diagonal(self):
        return self._upper_diagonal

    def set_first_row(self, val_b: Real, val_c: Real):
        self._diagonal[0] = val_b
        self._upper_diagonal[0] = val_c

    def set_mid_row(self, i: int, val_a: Real, val_b: Real, val_c: Real):
        qt_require(1 <= i <= self._n - 2,
                   "out of range in TridiagonalSystem.set_mid_row")
        self._lower_diagonal[i - 1] = val_a
        self._diagonal[i] = val_b
        self._upper_diagonal[i] = val_c

    def set_mid_rows(self, val_a: Real, val_b: Real, val_c: Real):
        for i in range(1, self._n - 1):
            self._lower_diagonal[i - 1] = val_a
            self._diagonal[i] = val_b
            self._upper_diagonal[i] = val_c

    def set_last_row(self, val_a: Real, val_b: Real):
        self._lower_diagonal[self._n - 2] = val_a
        self._diagonal[self._n - 1] = val_b

    def set_time(self, t: Real):
        if self._time_setter is not None:
            self._time_setter.set_time(t, self)

    def __pos__(self):
        """ +self """
        low = self._lower_diagonal
        mid = self._diagonal
        high = self._upper_diagonal
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result

    def __neg__(self):
        """ -self """
        low = [-i for i in self._lower_diagonal]
        mid = [-i for i in self._diagonal]
        high = [-i for i in self._upper_diagonal]
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result

    def __add__(self, other):
        """ self+other. """
        low = list(map(lambda a, b: a + b, self._lower_diagonal, other._lower_diagonal))
        mid = list(map(lambda a, b: a + b, self._diagonal, other._diagonal))
        high = list(map(lambda a, b: a + b, self._upper_diagonal, other._upper_diagonal))
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result

    def __sub__(self, other):
        """ self-other. """
        low = list(map(lambda a, b: a - b, self._lower_diagonal, other._lower_diagonal))
        mid = list(map(lambda a, b: a - b, self._diagonal, other._diagonal))
        high = list(map(lambda a, b: a - b, self._upper_diagonal, other._upper_diagonal))
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result

    def __mul__(self, n: Real):
        """ self*n. """
        low = [i * n for i in self._lower_diagonal]
        mid = [i * n for i in self._diagonal]
        high = [i * n for i in self._upper_diagonal]
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result

    def __truediv__(self, n: Real):
        """ self/n. """
        low = [i / n for i in self._lower_diagonal]
        mid = [i / n for i in self._diagonal]
        high = [i / n for i in self._upper_diagonal]
        result = TridiagonalOperator(low=low, mid=mid, high=high)
        return result
