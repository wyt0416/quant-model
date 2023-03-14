import sys
from enum import Enum
from typing import List, Optional

import numpy as np

from qtmodel.error import qt_require, QTError
from qtmodel.math.interpolation import InterpolationTemplateImpl, Interpolation
from qtmodel.methods.finitedifferences.tridiagonaloperator import TridiagonalOperator
from qtmodel.types import Real


class DerivativeApprox(Enum):
    # Spline approximation (non-local, non-monotonic, linear[?]).
    # Different boundary conditions can be used on the left and right
    # boundaries: see BoundaryCondition.
    Spline = 0

    # Overshooting minimization 1st derivative
    SplineOM1 = 1

    # Overshooting minimization 2nd derivative
    SplineOM2 = 2

    # Fourth-order approximation (local, non-monotonic, linear)
    FourthOrder = 3

    # Parabolic approximation (local, non-monotonic, linear)
    Parabolic = 4

    # Fritsch-Butland approximation (local, monotonic, non-linear)
    FritschButland = 5

    # Akima approximation (local, non-monotonic, non-linear)
    Akima = 6

    # Kruger approximation (local, monotonic, non-linear)
    Kruger = 7

    # Weighted harmonic mean approximation (local, monotonic, non-linear)
    Harmonic = 8


class BoundaryCondition(Enum):
    # Make second(-last) point an inactive knot
    NotAKnot = 0

    # Match value of end-slope
    FirstDerivative = 1

    # Match value of second derivative at end
    SecondDerivative = 2

    # Match first and second derivative at either end
    Periodic = 3

    # Match end-slope to the slope of the cubic that matches
    # the first four data at the respective end
    Lagrange = 4


class CoefficientHolder:
    def __init__(self, n: int):
        self._n = n
        self._primitive_const: List[Real] = [None] * (n - 1)
        self._a: List[Real] = [None] * (n - 1)
        self._b: List[Real] = [None] * (n - 1)
        self._c: List[Real] = [None] * (n - 1)
        self._monotonicity_adjustments: List[bool] = [None] * n


class CubicInterpolationImpl(CoefficientHolder, InterpolationTemplateImpl):

    def __init__(self,
                 x: list,
                 y: list,
                 da: DerivativeApprox,
                 monotonic: bool,
                 left_condition: BoundaryCondition,
                 left_condition_value: Real,
                 right_condition: BoundaryCondition,
                 right_condition_value: Real):
        CoefficientHolder.__init__(self, len(x))
        InterpolationTemplateImpl.__init__(self, x, y, Cubic.required_points)
        self._da = da
        self._monotonic = monotonic
        self._left_type = left_condition
        self._right_type = right_condition
        self._left_value = left_condition_value
        self._right_value = right_condition_value
        self._tmp = [None] * self._n
        self._dx: List[Optional[Real]] = [None] * (self._n - 1)
        self._S: List[Optional[Real]] = [None] * (self._n - 1)
        self._L = TridiagonalOperator(size=self._n)

        if self._left_type == BoundaryCondition.Lagrange or self._right_type == BoundaryCondition.Lagrange:
            qt_require(len(x) >= 4,
                       f"Lagrange boundary condition requires at least 4 points ({len(x)} are given)")

    @staticmethod
    def cubic_interpolating_polynomial_derivative(a: Real, b: Real, c: Real, d: Real, u: Real, v: Real, w: Real,
                                                  z: Real, x: Real):
        return (-((((a - c) * (b - c) * (c - x) * z - (a - d) * (b - d) * (d - x) * w) * (a - x + b - x) + (
                    (a - c) * (b - c) * z - (a - d) * (b - d) * w) * (a - x) * (b - x)) * (a - b) + (
                              (a - c) * (a - d) * v - (b - c) * (b - d) * u) * (c - d) * (c - x) * (d - x) + (
                              (a - c) * (a - d) * (a - x) * v - (b - c) * (b - d) * (b - x) * u) * (c - x + d - x) * (
                              c - d))) / ((a - b) * (a - c) * (a - d) * (b - c) * (b - d) * (c - d))

    def update(self):

        i = 0
        while i < self._n - 1:
            self._dx[i] = self._x[i + 1] - self._x[i]
            self._S[i] = (self._y[i + 1] - self._y[i]) / self._dx[i]
            i += 1

        # first derivative approximation
        if self._da == DerivativeApprox.Spline:
            i = 1
            while i < self._n - 1:
                self._L.set_mid_row(i, self._dx[i], 2.0 * (self._dx[i] + self._dx[i - 1]), self._dx[i - 1])
                self._tmp[i] = 3.0 * (self._dx[i] * self._S[i - 1] + self._dx[i - 1] * self._S[i])
                i += 1

            # left boundary condition
            if self._left_type == BoundaryCondition.NotAKnot:
                # ignoring end condition value
                self._L.set_first_row(self._dx[1] * (self._dx[1] + self._dx[0]),
                                      (self._dx[0] + self._dx[1]) * (self._dx[0] + self._dx[1]))
                self._tmp[0] = self._S[0] * self._dx[1] * (2.0 * self._dx[1] + 3.0 * self._dx[0]) + self._S[1] * \
                               self._dx[0] * self._dx[0]
            elif self._left_type == BoundaryCondition.FirstDerivative:
                self._L.set_first_row(1.0, 0.0)
                self._tmp[0] = self._left_value
            elif self._left_type == BoundaryCondition.SecondDerivative:
                self._L.set_first_row(2.0, 1.0)
                self._tmp[0] = 3.0 * self._S[0] - self._left_value * self._dx[0] / 2.0
            elif self._left_type == BoundaryCondition.Periodic:
                QTError("this end condition is not implemented yet")
            elif (self._left_type == BoundaryCondition.Periodic) or (self._left_type == BoundaryCondition.Lagrange):
                self._L.set_first_row(1.0, 0.0)
                self._tmp[0] = self.cubic_interpolating_polynomial_derivative(self._x[0], self._x[1], self._x[2],
                                                                              self._x[3], self._y[0], self._y[1],
                                                                              self._y[2], self._y[3], self._x[0])
            else:
                QTError("unknown end condition")

            # right boundary condition
            if self._right_type == BoundaryCondition.NotAKnot:
                # ignoring end condition value
                self._L.set_last_row(
                    -(self._dx[self._n - 2] + self._dx[self._n - 3]) * (self._dx[self._n - 2] + self._dx[self._n - 3]),
                    -self._dx[self._n - 3] * (self._dx[self._n - 3] + self._dx[self._n - 2]))
                self._tmp[self._n - 1] = -self._S[self._n - 3] * self._dx[self._n - 2] * self._dx[self._n - 2] - \
                                         self._S[self._n - 2] * self._dx[self._n - 3] * (
                                                     3.0 * self._dx[self._n - 2] + 2.0 * self._dx[self._n - 3])
            elif self._right_type == BoundaryCondition.FirstDerivative:
                self._L.set_last_row(0.0, 1.0)
                self._tmp[self._n - 1] = self._right_value
            elif self._right_type == BoundaryCondition.SecondDerivative:
                self._L.set_last_row(1.0, 2.0)
                self._tmp[self._n - 1] = 3.0 * self._S[self._n - 2] + self._right_value * self._dx[self._n - 2] / 2.0
            elif self._right_type == BoundaryCondition.Periodic:
                QTError("this end condition is not implemented yet")
            elif (self._right_type == BoundaryCondition.Periodic) or (self._right_type == BoundaryCondition.Lagrange):
                self._L.set_last_row(0.0, 1.0)
                self._tmp[self._n - 1] = self.cubic_interpolating_polynomial_derivative(self._x[self._n - 4],
                                                                                        self._x[self._n - 3],
                                                                                        self._x[self._n - 2],
                                                                                        self._x[self._n - 1],
                                                                                        self._y[self._n - 4],
                                                                                        self._y[self._n - 3],
                                                                                        self._y[self._n - 2],
                                                                                        self._y[self._n - 1],
                                                                                        self._x[self._n - 1])
            else:
                QTError("unknown end condition")

            # solve the system
            self._L.solve_for(self._tmp, self._tmp)
        elif self._da == DerivativeApprox.SplineOM1:
            T_ = np.zeros((self._n - 2, self._n))
            i = 0
            while i < self._n - 2:
                T_[i, i] = self._dx[i] / 6.0
                T_[i, i + 1] = (self._dx[i + 1] + self._dx[i]) / 3.0
                T_[i, i + 2] = self._dx[i + 1] / 6.0
                i += 1
            self._S = np.zeros((self._n - 2, self._n))
            i = 0
            while i < self._n - 2:
                self._S[i, i] = 1.0 / self._dx[i]
                self._S[i, i + 1] = -(1.0 / self._dx[i + 1] + 1.0 / self._dx[i])
                self._S[i, i + 2] = 1.0 / self._dx[i + 1]
                i += 1
            Up_ = np.zeros((self._n, 2))
            Up_[0, 0] = 1
            Up_[self._n - 1, 1] = 1
            Us_ = np.zeros((self._n, self._n - 2))
            i = 0
            while i < self._n - 2:
                Us_[i + 1, i] = 1
                i += 1
            Z_ = np.dot(Us_, np.linalg.inv(np.dot(T_, Us_)))
            I_ = np.zeros((self._n, self._n))
            i = 0
            while i < self._n:
                I_[i, i] = 1
                i += 1
            V_ = np.dot((I_ - np.dot(Z_, T_)), Up_)
            W_ = np.dot(Z_, self._S)
            Q_ = np.zeros((self._n, self._n))
            Q_[0, 0] = 1.0 / (self._n - 1) * self._dx[0] * self._dx[0] * self._dx[0]
            Q_[0, 1] = 7.0 / 8 * 1.0 / (self._n - 1) * self._dx[0] * self._dx[0] * self._dx[0]
            i = 1
            while i < self._n - 1:
                Q_[i, i - 1] = 7.0 / 8 * 1.0 / (self._n - 1) * self._dx[i - 1] * self._dx[i - 1] * self._dx[i - 1]
                Q_[i, i] = 1.0 / (self._n - 1) * self._dx[i] * self._dx[i] * self._dx[i] + 1.0 / (self._n - 1) * \
                           self._dx[i - 1] * self._dx[i - 1] * self._dx[i - 1]
                Q_[i, i + 1] = 7.0 / 8 * 1.0 / (self._n - 1) * self._dx[i] * self._dx[i] * self._dx[i]
                i += 1
            Q_[self._n - 1, self._n - 2] = 7.0 / 8 * 1.0 / (self._n - 1) * self._dx[self._n - 2] * self._dx[
                self._n - 2] * self._dx[self._n - 2]
            Q_[self._n - 1, self._n - 1] = 1.0 / (self._n - 1) * self._dx[self._n - 2] * self._dx[self._n - 2] * \
                                           self._dx[self._n - 2]
            J_ = np.dot((I_ - np.dot(V_, np.linalg.inv(np.dot(V_.transpose(), Q_, V_)), V_.transpose(), Q_)), W_)
            Y_ = np.zeros(self._n)
            i = 0
            while i < self._n:
                Y_[i] = self._y[i]
                i += 1
            D_ = np.dot(J_, Y_)
            i = 0
            while i < self._n - 1:
                self._tmp[i] = (Y_[i + 1] - Y_[i]) / self._dx[i] - (2.0 * D_[i] + D_[i + 1]) * self._dx[i] / 6.0
                i += 1
            self._tmp[self._n - 1] = self._tmp[self._n - 2] + D_[self._n - 2] * self._dx[self._n - 2] + (
                        D_[self._n - 1] - D_[self._n - 2]) * self._dx[self._n - 2] / 2.0

        elif self._da == DerivativeApprox.SplineOM2:
            T_ = np.zeros((self._n - 2, self._n))
            i = 0
            while i < self._n - 2:
                T_[i, i] = self._dx[i] / 6.0
                T_[i, i + 1] = (self._dx[i] + self._dx[i + 1]) / 3.0
                T_[i, i + 2] = self._dx[i + 1] / 6.0
                i += 1
            self._S = np.zeros((self._n - 2, self._n))
            i = 0
            while i < self._n - 2:
                self._S[i, i] = 1.0 / self._dx[i]
                self._S[i, i + 1] = -(1.0 / self._dx[i + 1] + 1.0 / self._dx[i])
                self._S[i, i + 2] = 1.0 / self._dx[i + 1]
                i += 1
            Up_ = np.zeros((self._n, 2))
            Up_[0, 0] = 1
            Up_[self._n - 1, 1] = 1
            Us_ = np.zeros((self._n, self._n - 2))
            i = 0
            while i < self._n - 2:
                Us_[i + 1, i] = 1
                i += 1
            Z_ = np.dot(Us_, np.linalg.inv(np.dot(T_, Us_)))
            I_ = np.zeros((self._n, self._n))
            i = 0
            while i < self._n:
                I_[i, i] = 1
                i += 1
            V_ = (I_ - Z_ * T_) * Up_
            W_ = Z_ * self._S
            Q_ = np.zeros((self._n, self._n))
            Q_[0, 0] = 1.0 / (self._n - 1) * self._dx[0]
            Q_[0, 1] = 1.0 / 2 * 1.0 / (self._n - 1) * self._dx[0]
            i = 1
            while i < self._n - 1:
                Q_[i, i - 1] = 1.0 / 2 * 1.0 / (self._n - 1) * self._dx[i - 1]
                Q_[i, i] = 1.0 / (self._n - 1) * self._dx[i] + 1.0 / (self._n - 1) * self._dx[i - 1]
                Q_[i, i + 1] = 1.0 / 2 * 1.0 / (self._n - 1) * self._dx[i]
                i += 1
            Q_[self._n - 1, self._n - 2] = 1.0 / 2 * 1.0 / (self._n - 1) * self._dx[self._n - 2]
            Q_[self._n - 1, self._n - 1] = 1.0 / (self._n - 1) * self._dx[self._n - 2]
            J_ = np.dot((I_ - np.dot(V_, np.linalg.inv(np.dot(V_.transpose(), Q_, V_)), V_.transpose(), Q_)), W_)
            Y_ = np.zeros(self._n)
            i = 0
            while i < self._n:
                Y_[i] = self._y[i]
                i += 1
            D_ = np.dot(J_, Y_)
            i = 0
            while i < self._n - 1:
                self._tmp[i] = (Y_[i + 1] - Y_[i]) / self._dx[i] - (2.0 * D_[i] + D_[i + 1]) * self._dx[i] / 6.0
                i += 1
            self._tmp[self._n - 1] = self._tmp[self._n - 2] + D_[self._n - 2] * self._dx[self._n - 2] + (
                        D_[self._n - 1] - D_[self._n - 2]) * self._dx[self._n - 2] / 2.0
        else:
            if self._n == 2:
                self._tmp[0] = self._tmp[1] = self._S[0]
            else:
                if self._da == DerivativeApprox.FourthOrder:
                    QTError("FourthOrder not implemented yet")
                elif self._da == DerivativeApprox.Parabolic:
                    # intermediate points
                    i = 1
                    while i < self._n - 1:
                        self._tmp[i] = (self._dx[i - 1] * self._S[i] + self._dx[i] * self._S[i - 1]) / (
                                    self._dx[i] + self._dx[i - 1])
                        i += 1
                    # end points
                    self._tmp[0] = ((2.0 * self._dx[0] + self._dx[1]) * self._S[0] - self._dx[0] * self._S[1]) / (
                                self._dx[0] + self._dx[1])
                    self._tmp[self._n - 1] = ((2.0 * self._dx[self._n - 2] + self._dx[self._n - 3]) * self._S[
                        self._n - 2] - self._dx[self._n - 2] * self._S[self._n - 3]) / (
                                                         self._dx[self._n - 2] + self._dx[self._n - 3])
                elif self._da == DerivativeApprox.FritschButland:
                    # intermediate points
                    i = 1
                    while i < self._n - 1:
                        Smin = min(self._S[i - 1], self._S[i])
                        Smax = max(self._S[i - 1], self._S[i])
                        if Smax + 2.0 * Smin == 0:
                            if Smin * Smax < 0:
                                self._tmp[i] = -sys.float_info.max
                            elif Smin * Smax == 0:
                                self._tmp[i] = 0
                            else:
                                self._tmp[i] = sys.float_info.max
                        else:
                            self._tmp[i] = 3.0 * Smin * Smax / (Smax + 2.0 * Smin)
                        i += 1
                    # end points
                    self._tmp[0] = ((2.0 * self._dx[0] + self._dx[1]) * self._S[0] - self._dx[0] * self._S[1]) / (
                                self._dx[0] + self._dx[1])
                    self._tmp[self._n - 1] = ((2.0 * self._dx[self._n - 2] + self._dx[self._n - 3]) * self._S[
                        self._n - 2] - self._dx[self._n - 2] * self._S[self._n - 3]) / (
                                                         self._dx[self._n - 2] + self._dx[self._n - 3])
                elif self._da == DerivativeApprox.Akima:
                    self._tmp[0] = (abs(self._S[1] - self._S[0]) * 2 * self._S[0] * self._S[1] + abs(
                        2 * self._S[0] * self._S[1] - 4 * self._S[0] * self._S[0] * self._S[1]) * self._S[0]) / (
                                           abs(self._S[1] - self._S[0]) + abs(
                                       2 * self._S[0] * self._S[1] - 4 * self._S[0] * self._S[0] * self._S[1]))
                    self._tmp[1] = (abs(self._S[2] - self._S[1]) * self._S[0] + abs(
                        self._S[0] - 2 * self._S[0] * self._S[1]) * self._S[1]) / (
                                           abs(self._S[2] - self._S[1]) + abs(self._S[0] - 2 * self._S[0] * self._S[1]))
                    i = 2
                    while i < self._n - 2:
                        if (self._S[i - 2] == self._S[i - 1]) and (self._S[i] != self._S[i + 1]):
                            self._tmp[i] = self._S[i - 1]
                        elif (self._S[i - 2] != self._S[i - 1]) and (self._S[i] == self._S[i + 1]):
                            self._tmp[i] = self._S[i]
                        elif self._S[i] == self._S[i - 1]:
                            self._tmp[i] = self._S[i]
                        elif (self._S[i - 2] == self._S[i - 1]) and (self._S[i - 1] != self._S[i]) and (
                                self._S[i] == self._S[i + 1]):
                            self._tmp[i] = (self._S[i - 1] + self._S[i]) / 2.0
                        else:
                            self._tmp[i] = (abs(self._S[i + 1] - self._S[i]) * self._S[i - 1] + abs(
                                self._S[i - 1] - self._S[i - 2]) * self._S[i]) / (
                                                   abs(self._S[i + 1] - self._S[i]) + abs(
                                               self._S[i - 1] - self._S[i - 2]))
                        i += 1
                    self._tmp[self._n - 2] = (abs(2 * self._S[self._n - 2] * self._S[self._n - 3] - self._S[
                        self._n - 2]) * self._S[self._n - 3] + abs(
                        self._S[self._n - 3] - self._S[self._n - 4]) * self._S[self._n - 2]) / (
                                                         abs(2 * self._S[self._n - 2] * self._S[self._n - 3] - self._S[
                                                             self._n - 2]) + abs(
                                                     self._S[self._n - 3] - self._S[self._n - 4]))
                    self._tmp[self._n - 1] = (abs(4 * self._S[self._n - 2] * self._S[self._n - 2] * self._S[
                        self._n - 3] - 2 * self._S[self._n - 2] * self._S[self._n - 3]) * self._S[
                                                  self._n - 2] + abs(self._S[self._n - 2] - self._S[self._n - 3]) * 2 *
                                              self._S[self._n - 2] * self._S[self._n - 3]) / (
                                                     abs(4 * self._S[self._n - 2] * self._S[self._n - 2] * self._S[
                                                         self._n - 3] - 2 * self._S[self._n - 2] * self._S[
                                                             self._n - 3]) + abs(
                                                 self._S[self._n - 2] - self._S[self._n - 3]))
                elif self._da == DerivativeApprox.Kruger:
                    # intermediate points
                    i = 1
                    while i < self._n - 1:
                        if self._S[i - 1] * self._S[i] < 0.0:
                            # slope changes sign at point
                            self._tmp[i] = 0.0
                        else:
                            # slope will be between the slopes of the adjacent
                            # straight lines and should approach zero if the
                            # slope of either line approaches zero
                            self._tmp[i] = 2.0 / (1.0 / self._S[i - 1] + 1.0 / self._S[i])
                        i += 1
                    # end points
                    self._tmp[0] = (3.0 * self._S[0] - self._tmp[1]) / 2.0
                    self._tmp[self._n - 1] = (3.0 * self._S[self._n - 2] - self._tmp[self._n - 2]) / 2.0
                elif self._da == DerivativeApprox.Harmonic:
                    # intermediate points
                    i = 1
                    while i < self._n - 1:
                        w1 = 2 * self._dx[i] + self._dx[i - 1]
                        w2 = self._dx[i] + 2 * self._dx[i - 1]
                        if self._S[i - 1] * self._S[i] <= 0.0:
                            # slope changes sign at point
                            self._tmp[i] = 0.0
                        else:
                            # weighted harmonic mean of self._S[i] and S_[i-1] if they
                            # have the same sign; otherwise 0
                            self._tmp[i] = (w1 + w2) / (w1 / self._S[i - 1] + w2 / self._S[i])
                        i += 1
                    # end points [0]
                    self._tmp[0] = ((2 * self._dx[0] + self._dx[1]) * self._S[0] - self._dx[0] * self._S[1]) / (
                                self._dx[1] + self._dx[0])
                    if self._tmp[0] * self._S[0] < 0.0:
                        self._tmp[0] = 0
                    elif self._S[0] * self._S[1] < 0:
                        if abs(self._tmp[0]) > abs(3 * self._S[0]):
                            self._tmp[0] = 3 * self._S[0]
                    # end points [n-1]
                    self._tmp[self._n - 1] = ((2 * self._dx[self._n - 2] + self._dx[self._n - 3]) * self._S[
                        self._n - 2] - self._dx[self._n - 2] * self._S[self._n - 3]) / (
                                                     self._dx[self._n - 3] + self._dx[self._n - 2])
                    if self._tmp[self._n - 1] * self._S[self._n - 2] < 0.0:
                        self._tmp[self._n - 1] = 0
                    elif self._S[self._n - 2] * self._S[self._n - 3] < 0:
                        if abs(self._tmp[self._n - 1]) > abs(3 * self._S[self._n - 2]):
                            self._tmp[self._n - 1] = 3 * self._S[self._n - 2]
                else:
                    QTError("unknown scheme")

        self._monotonicity_adjustments = [False] * len(self._monotonicity_adjustments)
        # Hyman monotonicity constrained filter
        if self._monotonic:
            i = 0
            while i < self._n:
                if i == 0:
                    if self._tmp[i] * self._S[0] > 0.0:
                        correction = self._tmp[i] / abs(self._tmp[i]) * min(
                        abs(self._tmp[i]), abs(3.0 * self._S[0]))
                    else:
                        correction = 0.0
                    if correction is not self._tmp[i]:
                        self._tmp[i] = correction
                        self._monotonicity_adjustments[i] = True
                elif i == self._n - 1:
                    if self._tmp[i] * self._S[self._n - 2] > 0.0:
                        correction = self._tmp[i] / abs(self._tmp[i]) * min(
                        abs(self._tmp[i]), abs(3.0 * self._S[self._n - 2]))
                    else:
                        correction = 0.0
                    if correction is not self._tmp[i]:
                        self._tmp[i] = correction
                        self._monotonicity_adjustments[i] = True
                else:
                    pm = (self._S[i - 1] * self._dx[i] + self._S[i] * self._dx[i - 1]) / (self._dx[i - 1] + self._dx[i])
                    M = 3.0 * min(min(abs(self._S[i - 1]), abs(self._S[i])), abs(pm))
                    if i > 1:
                        if (self._S[i - 1] - self._S[i - 2]) * (self._S[i] - self._S[i - 1]) > 0.0:
                            pd = (self._S[i - 1] * (2.0 * self._dx[i - 1] + self._dx[i - 2]) - self._S[i - 2] *
                                  self._dx[i - 1]) / (
                                         self._dx[i - 2] + self._dx[i - 1])
                            if pm * pd > 0.0 and pm * (self._S[i - 1] - self._S[i - 2]) > 0.0:
                                M = max(M, 1.5 * min(abs(pm), abs(pd)))
                    if i < self._n - 2:
                        if (self._S[i] - self._S[i - 1]) * (self._S[i + 1] - self._S[i]) > 0.0:
                            pu = (self._S[i] * (2.0 * self._dx[i] + self._dx[i + 1]) - self._S[i + 1] * self._dx[i]) / (
                                        self._dx[i] + self._dx[i + 1])
                            if pm * pu > 0.0 and -pm * (self._S[i] - self._S[i - 1]) > 0.0:
                                M = max(M, 1.5 * min(abs(pm), abs(pu)))
                    if self._tmp[i] * pm > 0.0:
                        correction = self._tmp[i] / abs(self._tmp[i]) * min(abs(self._tmp[i]), M)
                    else:
                        correction = 0.0
                    if correction is not self._tmp[i]:
                        self._tmp[i] = correction
                        self._monotonicity_adjustments[i] = True
                i += 1

        # cubic coefficients
        i = 0
        while i < self._n - 1:
            self._a[i] = self._tmp[i]
            self._b[i] = (3.0 * self._S[i] - self._tmp[i + 1] - 2.0 * self._tmp[i]) / self._dx[i]
            self._c[i] = (self._tmp[i + 1] + self._tmp[i] - 2.0 * self._S[i]) / (self._dx[i] * self._dx[i])
            i += 1

        self._primitive_const[0] = 0.0
        i = 1
        while i < self._n - 1:
            self._primitive_const[i] = self._primitive_const[i - 1] + self._dx[i - 1] * (
                        self._y[i - 1] + self._dx[i - 1] * (
                        self._a[i - 1] / 2.0 + self._dx[i - 1] * (
                            self._b[i - 1] / 3.0 + self._dx[i - 1] * self._c[i - 1] / 4.0)))
            i += 1

    def value(self, x: Real):
        j = self.locate(x)
        self._dx = x - self._x[j]
        return self._y[j] + self._dx * (self._a[j] + self._dx * (self._b[j] + self._dx * self._c[j]))

    def primitive(self, x: Real):
        j = self.locate(x)
        self._dx = x - self._x[j]
        return self._primitive_const[j] + self._dx * (self._y[j] + self._dx * (
                    self._a[j] / 2.0 + self._dx * (self._b[j] / 3.0 + self._dx * self._c[j] / 4.0)))

    def derivative(self, x: Real):
        j = self.locate(x)
        self._dx = x - self._x[j]
        return self._a[j] + (2.0 * self._b[j] + 3.0 * self._c[j] * self._dx) * self._dx

    def second_derivative(self, x: Real):
        j = self.locate(x)
        self._dx = x - self._x[j]
        return 2.0 * self._b[j] + 6.0 * self._c[j] * self._dx


class CubicInterpolation(Interpolation):
    """ Cubic interpolation between discrete points. """

    def __init__(self,
                 x: list,
                 y: list,
                 da: DerivativeApprox,
                 monotonic: bool,
                 left_cond: BoundaryCondition,
                 left_condition_value: Real,
                 right_cond: BoundaryCondition,
                 right_condition_value: Real):
        super(CubicInterpolation, self).__init__()
        self._impl = CubicInterpolationImpl(x, y,
                                            da,
                                            monotonic,
                                            left_cond,
                                            left_condition_value,
                                            right_cond,
                                            right_condition_value)
        self._impl.update()

    def coeffs(self):
        return self._impl

    def primitive_constants(self):
        return self.coeffs()._primitive_const

    def a_coefficients(self):
        return self.coeffs()._a

    def b_coefficients(self):
        return self.coeffs()._b

    def c_coefficients(self):
        return self.coeffs()._c

    def monotonicity_adjustments(self):
        return self.coeffs()._monotonicity_adjustments


class CubicNaturalSpline(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Spline,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class MonotonicCubicNaturalSpline(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Spline,
                         True,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class CubicSplineOvershootingMinimization1(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.SplineOM1,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class CubicSplineOvershootingMinimization2(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.SplineOM2,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class AkimaCubicInterpolation(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Akima,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class KrugerCubic(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Kruger,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class HarmonicCubic(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Harmonic,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class FritschButlandCubic(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.FritschButland,
                         True,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class Parabolic(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Parabolic,
                         False,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class MonotonicParabolic(CubicInterpolation):

    def __init__(self, x: list, y: list):
        super().__init__(x,
                         y,
                         DerivativeApprox.Parabolic,
                         True,
                         BoundaryCondition.SecondDerivative,
                         0.0,
                         BoundaryCondition.SecondDerivative,
                         0.0)


class Cubic:
    """ Cubic interpolation factory and traits """
    global_ = True
    required_points = 2

    def __init__(self,
                 da=DerivativeApprox.Kruger,
                 monotonic=False,
                 left_condition=BoundaryCondition.SecondDerivative,
                 left_condition_value=0.0,
                 right_condition=BoundaryCondition.SecondDerivative,
                 right_condition_value=0.0):
        self._da = da
        self._monotonic = monotonic
        self._left_type = left_condition
        self._right_type = right_condition
        self._left_value = left_condition_value
        self._right_value = right_condition_value

    def interpolate(self, x: list, y: list):
        return CubicInterpolation(x, y,
                                  self._da, self._monotonic,
                                  self._left_type, self._left_value,
                                  self._right_type, self._right_value)
