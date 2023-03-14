import math
from enum import Enum
from typing import List, Any

import numpy as np

from qtmodel.error import qt_require


class EigenVectorCalculationTypes(Enum):
    WithEigenVector = "With Eigen Vector"
    WithoutEigenVector = "Without Eigen Vector"
    OnlyFirstRowEigenVector = "Only First Row Eigen Vector"


class ShiftStrategyTypes(Enum):
    NoShift = "No Shift"
    Overrelaxation = "Over Relaxation"
    CloseEigenValue = "Close Eigen Value"


class TqrEigenDecomposition:
    """
    tridiag. QR eigen decomposition with explicite shift aka Wilkinson
    References:

    Wilkinson, J.H. and Reinsch, C. 1971, Linear Algebra, vol. II of
    Handbook for Automatic Computation (New York: Springer-Verlag)

    "Numerical Recipes in C", 2nd edition,
    Press, Teukolsky, Vetterling, Flannery,
    """

    def __init__(
            self,
            diag: List[Any],
            sub: List[Any],
            calc: EigenVectorCalculationTypes = EigenVectorCalculationTypes.WithEigenVector,
            strategy: ShiftStrategyTypes = ShiftStrategyTypes.CloseEigenValue):
        self._iter = 0
        self._d = diag
        rows = len(diag) if calc == EigenVectorCalculationTypes.WithEigenVector else (
            0 if calc == EigenVectorCalculationTypes.WithoutEigenVector else 1)
        self._ev = np.zeros((rows, len(diag)))

        n = len(diag)
        qt_require(n == len(sub) + 1, "Wrong dimensions")

        e = [0.0] * n
        e[1:] = sub
        i = 0
        while i < self._ev.shape[0]:
            self._ev[i, i] = 1.0
            i += 1

        k = n - 1
        while k >= 1:
            while not self.off_diag_is_zero(k, e):
                l = k
                l -= 1
                while l > 0 and not self.off_diag_is_zero(l, e):
                    l -= 1
                self._iter += 1

                q = self._d[l]
                if strategy != ShiftStrategyTypes.NoShift:
                    # calculated eigenvalue of 2x2 sub matrix of
                    # [ d_[k-1] e_[k] ]
                    # [  e_[k]  d_[k] ]
                    # which is closer to d_[k+1].
                    # FLOATING_POINT_EXCEPTION
                    t1 = math.sqrt(
                        0.25 * (self._d[k] * self._d[k] + self._d[k - 1] * self._d[k - 1]) - 0.5 * self._d[k - 1] *
                        self._d[k] + e[k] * e[k])
                    t2 = 0.5 * (self._d[k] + self._d[k - 1])

                    lambda_ = t2 + t1 if (abs(t2 + t1 - self._d[k]) < abs(t2 - t1 - self._d[k])) else t2 - t1

                    if strategy == ShiftStrategyTypes.CloseEigenValue:
                        q -= lambda_
                    else:
                        q -= (1.25 if (k == n - 1) else 1.0) * lambda_

                # the QR transformation
                sine = 1.0
                cosine = 1.0
                u = 0.0

                recover_underflow = False
                i = l + 1
                while i <= k and not recover_underflow:
                    h = cosine * e[i]
                    p = sine * e[i]

                    e[i - 1] = math.sqrt(p * p + q * q)
                    if e[i - 1] != 0.0:
                        sine = p / e[i - 1]
                        cosine = q / e[i - 1]

                        g = self._d[i - 1] - u
                        t = (self._d[i] - g) * sine + 2 * cosine * h

                        u = sine * t
                        self._d[i - 1] = g + u
                        q = cosine * t - h

                        j = 0
                        while j < self._ev.shape[0]:
                            tmp = self._ev[j, i - 1]
                            self._ev[j, i - 1] = sine * self._ev[j, i] + cosine * tmp
                            self._ev[j, i] = cosine * self._ev[j, i] - sine * tmp
                            j += 1
                    else:
                        # recover from underflow
                        self._d[i - 1] -= u
                        e[l] = 0.0
                        recover_underflow = True
                    i += 1

                if not recover_underflow:
                    self._d[k] -= u
                    e[k] = q
                    e[l] = 0.0

            k -= 1

        # sort (eigenvalues, eigenvectors), code taken from
        # symmetricschuredecomposition.py
        temp: List[Any] = [()] * n
        eigen_vector = [] * self._ev.shape[0]
        i = 0
        while i < n:
            if self._ev.shape[0] > 0:
                eigen_vector = self._ev[:, i]
            temp[i] = (self._d[i], list(eigen_vector))
            i += 1
        temp.sort(reverse=True)
        # first element is positive
        i = 0
        while i < n:
            self._d[i] = temp[i][0]
            sign = 1.0
            if self._ev.shape[0] > 0 and temp[i][1][0] < 0.0:
                sign = -1.0
            j = 0
            while j < self._ev.shape[0]:
                self._ev[j, i] = sign * temp[i][1][j]
                j += 1
            i += 1

    def eigenvalues(self):
        return self._d

    def eigenvectors(self):
        return self._ev

    def iterations(self):
        return self._iter

    def off_diag_is_zero(self, k: int, e: List[Any]):
        """
        see NR for abort assumption as it is not part of the original Wilkinson algorithm
        :param k:
        :param e:
        :return:
        """
        return abs(self._d[k - 1]) + abs(self._d[k]
                                         ) == abs(self._d[k - 1]) + abs(self._d[k]) + abs(e[k])
