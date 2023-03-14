import copy
import math
from typing import Callable, Union, List

from qtmodel.error import QTError
from qtmodel.types import Real


class OdeFctWrapper:

    def __init__(self, ode1d):
        self._ode1d = ode1d

    def __call__(self, x: Real, y: list):
        res = [self._ode1d(x, y[0])]
        return res


class AdaptiveRungeKutta:
    OdeFct = Callable[[Real, list], list]
    OdeFct1d = Callable[[Real, Real], Real]

    def __init__(self,
                 eps: Real = 1.0e-6,
                 h1: Real = 1.0e-4,
                 hmin: Real = 0.0):
        """
        The class is constructed with the following inputs:
            - eps       prescribed error for the solution
            - h1        start step size
            - hmin      smallest step size allowed
        """
        self._eps = eps
        self._h1 = h1
        self._hmin = hmin
        self.a2 = 0.2
        self.a3 = 0.3
        self.a4 = 0.6
        self.a5 = 1.0
        self.a6 = 0.875
        self.b21 = 0.2
        self.b41 = 0.3
        self.b42 = -0.9
        self.b43 = 1.2
        self.b52 = 2.5
        self.ADAPTIVERK_MAXSTP = 10000
        self.ADAPTIVERK_TINY = 1.0E-30
        self.ADAPTIVERK_SAFETY = 0.9
        self.ADAPTIVERK_PGROW = -0.2
        self.ADAPTIVERK_PSHRINK = -0.25
        self.ADAPTIVERK_ERRCON = 1.89E-4
        self.b31 = 3.0 / 40.0
        self.b32 = 9.0 / 40.0
        self.b51 = -11.0 / 54.0
        self.b53 = -70.0 / 27.0
        self.b54 = 35.0 / 27.0
        self.b61 = 1631.0 / 55296.0
        self.b62 = 175.0 / 512.0
        self.b63 = 575.0 / 13824.0
        self.b64 = 44275.0 / 110592.0
        self.b65 = 253.0 / 4096.0
        self.c1 = 37.0 / 378.0
        self.c3 = 250.0 / 621.0
        self.c4 = 125.0 / 594.0
        self.c6 = 512.0 / 1771.0
        self.dc1 = self.c1 - 2825.0 / 27648.0
        self.dc3 = self.c3 - 18575.0 / 48384.0
        self.dc4 = self.c4 - 13525.0 / 55296.0
        self.dc5 = -277.0 / 14336.0
        self.dc6 = self.c6 - 0.25

    def __call__(self,
                 ode: Union[OdeFct, OdeFct1d],
                 y1: Union[List[Real], Real],
                 x1: Real,
                 x2: Real):
        if isinstance(y1, list):
            n = len(y1)
            y = copy.deepcopy(y1)
            y_scale = [None] * n
            x = x1
            h = self._h1 * (1 if x1 <= x2 else -1)
            hnext = hdid = None

            for nstp in range(1, self.ADAPTIVERK_MAXSTP + 1):
                dydx = ode(x, y)
                for i in range(n):
                    y_scale[i] = abs(y[i]) + abs(dydx[i] * h) + self.ADAPTIVERK_TINY
                if (x + h - x2) * (x + h - x1) > 0.0:
                    h = x2 - x
                x, hdid, hnext = self.rkqs(y, dydx, x, h, self._eps, y_scale, hdid, hnext, ode)

                if (x - x2) * (x2 - x1) >= 0.0:
                    return y

                if abs(hnext) <= self._hmin:
                    QTError(f"Step size ({hnext}) too small ({self._hmin} min) in AdaptiveRungeKutta")
                h = hnext
            QTError(f"Too many steps ({self.ADAPTIVERK_MAXSTP}) in AdaptiveRungeKutta")

        else:
            return self.__call__(OdeFctWrapper(ode), [y1], x1, x2)[0]

    def rkqs(self,
             y: list,
             dydx: list,
             x: Real,
             htry: Real,
             eps: Real,
             y_scale: list,
             hdid: Real,
             hnext: Real,
             derivs: OdeFct):
        n = len(y)
        yerr = [None] * n
        ytemp = [None] * n

        h = htry

        while 1:
            self.rkck(y, dydx, x, h, ytemp, yerr, derivs)
            errmax = 0.0
            for i in range(n):
                errmax = max(errmax, abs(yerr[i] / y_scale[i]))
            errmax /= eps
            if errmax > 1.0:
                htemp1 = self.ADAPTIVERK_SAFETY * h * math.pow(errmax, self.ADAPTIVERK_PSHRINK)
                htemp2 = h / 10
                # These would be min and max, of course,
                # but VC++14 had problems inlining them and caused
                # the wrong results to be calculated.  The problem
                # seems to be fixed in update 3, but let's keep this
                # implementation for compatibility.
                max_positive = htemp1 if htemp1 > htemp2 else htemp2
                max_negative = htemp1 if htemp1 < htemp2 else htemp2
                h = max_positive if (h >= 0.0) else max_negative
                xnew = x + h
                if xnew == x:
                    QTError(f"Stepsize underflow ({h} at x = {x}) in AdaptiveRungeKutta.rkqs")
                continue
            else:
                if errmax > self.ADAPTIVERK_ERRCON:
                    hnext = self.ADAPTIVERK_SAFETY * h * math.pow(errmax, self.ADAPTIVERK_PGROW)
                else:
                    hnext = 5.0 * h
                hdid = h
                x += hdid
                for i in range(n):
                    y[i] = ytemp[i]
                break
        return x, hdid, hnext

    def rkck(self,
             y: list,
             dydx: list,
             x: Real,
             h: Real,
             yout: list,
             yerr: list,
             derivs: OdeFct):

        n = len(y)
        ytemp = [None] * n

        # first step
        for i in range(n):
            ytemp[i] = y[i] + self.b21 * h * dydx[i]

        # second step
        ak2 = derivs(x + self.a2 * h, ytemp)
        for i in range(n):
            ytemp[i] = y[i] + h * (self.b31 * dydx[i] + self.b32 * ak2[i])

        # third step
        ak3 = derivs(x + self.a3 * h, ytemp)
        for i in range(n):
            ytemp[i] = y[i] + h * (self.b41 * dydx[i] + self.b42 * ak2[i] + self.b43 * ak3[i])

        # fourth step
        ak4 = derivs(x + self.a4 * h, ytemp)
        for i in range(n):
            ytemp[i] = y[i] + h * (self.b51 * dydx[i] + self.b52 * ak2[i] + self.b53 * ak3[i] + self.b54 * ak4[i])

        # fifth step
        ak5 = derivs(x + self.a5 * h, ytemp)
        for i in range(n):
            ytemp[i] = y[i] + h * (
                    self.b61 * dydx[i] + self.b62 * ak2[i] + self.b63 * ak3[i] + self.b64 * ak4[i] + self.b65 * ak5[
                i])

        # sixth step
        ak6 = derivs(x + self.a6 * h, ytemp)
        for i in range(n):
            yout[i] = y[i] + h * (self.c1 * dydx[i] + self.c3 * ak3[i] + self.c4 * ak4[i] + self.c6 * ak6[i])
            yerr[i] = h * (
                    self.dc1 * dydx[i] + self.dc3 * ak3[i] + self.dc4 * ak4[i] + self.dc5 * ak5[i] + self.dc6 * ak6[
                i])
