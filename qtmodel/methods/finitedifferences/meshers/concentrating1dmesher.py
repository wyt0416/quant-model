import math
import sys
from typing import List, Union, Tuple

from qtmodel.error import qt_require
from qtmodel.math.comparison import close, close_enough
from qtmodel.math.interpolations.linearinterpolation import LinearInterpolation
from qtmodel.math.ode.adaptiverungekutta import AdaptiveRungeKutta
from qtmodel.math.solvers1d.brent import Brent
from qtmodel.methods.finitedifferences.meshers.fdm1dmesher import Fdm1dMesher
from qtmodel.types import Real


class OdeIntegrationFct(object):
    def __init__(self, points: List = None, betas: List = None, tol: Real = None):
        self._rk = AdaptiveRungeKutta(tol)
        self._points = points
        self._betas = betas

    def solve(self, a: Real, y0: Real, x0: Real, x1: Real):
        ode_fct = lambda x, y: self.jac(a, x, y)
        return self._rk(ode_fct, y0, x0, x1)

    def jac(self, a: Real, unnamed_parameer: Real, y: Real):
        s = 0.0
        i = 0
        while i < len(self._points):
            s += 1.0 / (self._betas[i] + pow(y - self._points[i], 2))
            i += 1
        return a / math.sqrt(s)


def equal_on_first(p1: Tuple[Real, Real], p2: Tuple[Real, Real]):
    return close_enough(p1[0], p2[0], 1000)


class Concentrating1dMesher(Fdm1dMesher):
    def __init__(self,
                 start: Real,
                 end: Real,
                 size: int,
                 c_points: Union[Tuple[Real, Real], List[Tuple[Real, Real, bool]]] = (None, None),
                 require_c_point: bool = False,
                 tol: Real = 1e-8):
        super().__init__(size)
        qt_require(end > start, "end must be larger than start")
        if isinstance(c_points, tuple):
            c_point = c_points[0]
            density = None if c_points[1] is None else c_points[1] * (end - start)

            qt_require(c_point is None or (start <= c_point <= end), "cPoint must be between start and end")
            qt_require(density is None or density > 0.0, "density > 0 required")
            qt_require(c_point is None or density is not None, "density must be given if cPoint is given")
            qt_require((not require_c_point) or c_point is not None, "cPoint is required in grid but not given")

            dx = 1.0 / (size - 1)

            if c_point is not None:
                u = []
                z = []
                c1 = math.asinh((start - c_point) / density)
                c2 = math.asinh((end - c_point) / density)
                if require_c_point:
                    u.append(0.0)
                    z.append(0.0)
                    if (not close(c_point, start)) and not close(c_point, end):
                        z0 = -c1 / (c2 - c1)
                        u0 = max(min(round(z0 * (size - 1)), int(size) - 2), 1) / (size - 1)
                        u.append(u0)
                        z.append(z0)
                    u.append(1.0)
                    z.append(1.0)
                    transform = LinearInterpolation(u, z)

                i = 1
                while i < size - 1:
                    li = transform(i * dx) if require_c_point else i * dx
                    self._locations[i] = c_point + density * math.sinh(c1 * (1.0 - li) + c2 * li)
                    i += 1
            else:
                i = 1
                while i < size - 1:
                    self._locations[i] = start + i * dx * (end - start)
                    i += 1

            self._locations[0] = start
            self._locations[-1] = end

            i = 0
            while i < size - 1:
                self._dplus[i] = self._dminus[i + 1] = self._locations[i + 1] - self._locations[i]
                i += 1
            self._dplus[-1] = self._dminus[0] = sys.float_info.max

        else:
            points = []
            betas = []
            for c_point in c_points:
                points.append(c_point[0])
                betas.append(pow(c_point[1] * (end - start), 2))

            # get scaling factor a so that y(1) = end
            a_init = 0.0
            i = 0
            while i < len(points):
                c1 = math.asinh((start - points[i]) / betas[i])
                c2 = math.asinh((end - points[i]) / betas[i])
                a_init += (c2 - c1) / len(points)
                i += 1

            fct = OdeIntegrationFct(points, betas, tol)
            a = Brent().solve(lambda x: fct.solve(x, start, 0.0, 1.0) - end, tol, a_init, 0.1 * a_init)

            # solve ODE for all grid points
            x = [None] * size
            y = [None] * size
            x[0] = 0.0
            y[0] = start
            dx = 1.0 / (size - 1)
            i = 1
            while i < size:
                x[i] = i * dx
                y[i] = fct.solve(a, y[i - 1], x[i - 1], x[i])
                i += 1

            # eliminate numerical noise and ensure y(1) = end
            dy = y[-1] - end
            i = 1
            while i < size:
                y[i] -= i * dx * dy
                i += 1

            ode_solution = LinearInterpolation(x, y)

            # ensure required points are part of the grid
            w = [(0.0, 0.0)]

            i = 0
            while i < len(points):
                if c_points[i][2] and start < points[i] < end:
                    j = sum(k<points[i] for k in y)

                    e = Brent().solve(lambda x: ode_solution(x, True) - points[i], sys.float_info.epsilon, x[j],
                                      0.5 / size)

                    w.append((min(x[size - 2], x[j]), e))
                i += 1
            w.append((1.0, 1.0))
            w.sort()
            r = set()
            for i in range(len(w)):
                for j in range(i + 1, len(w)):
                    if equal_on_first(w[i], w[j]):
                        r.add(j)

            w = [w[i] for i in range(len(w)) if i not in r]

            u = [None] * len(w)
            z = [None] * len(w)
            i = 0
            while i < len(w):
                u[i] = w[i][0]
                z[i] = w[i][1]
                i += 1
            transform = LinearInterpolation(u, z)

            i = 0
            while i < size:
                self._locations[i] = ode_solution(transform(i * dx))
                i += 1

            i = 0
            while i < size - 1:
                self._dplus[i] = self._dminus[i + 1] = self._locations[i + 1] - self._locations[i]
                i += 1
            self._dplus[-1] = self._dminus[0] = None
