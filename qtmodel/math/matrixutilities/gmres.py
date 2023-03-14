"""
References:
Saad, Yousef. 1996, Iterative methods for sparse linear systems,
http://www-users.cs.umn.edu/~saad/books.html

Dongarra et al. 1994,
Templates for the Solution of Linear Systems: Building Blocks
for Iterative Methods, 2nd Edition, SIAM, Philadelphia
http://www.netlib.org/templates/templates.pdf

Christian Kanzow
Numerik linearer Gleichungssysteme (German)
Chapter 6: GMRES und verwandte Verfahren
http://bilder.buecher.de/zusatz/12/12950/12950560_lese_1.pdf
"""


import math
import sys
from collections import defaultdict
from typing import List, Callable

import numpy as np

from qtmodel.error import qt_require
from qtmodel.math.array import dot_product, norm_2
from qtmodel.types import Real


class GMRESResult:

    def __init__(self, errors: List, x: List):
        self.errors = errors
        self.x = x


class GMRES:

    def __init__(self,
                 A: Callable[[list], list],
                 max_iter: int,
                 rel_tol: Real,
                 pre_conditioner: Callable[[list], list] = None):

        self._A = A
        self._M = pre_conditioner
        self._max_iter = max_iter
        self._rel_tol = rel_tol

        qt_require(self._max_iter > 0, "max_iter must be greater than zero")

    def solve(self, b: list, x0: list):
        result = self.solve_impl(b, x0)

        qt_require(result.errors[-1] < self._rel_tol, "could not converge")
        return result

    def solve_with_restart(self, restart, b, x0):

        result = self.solve_impl(b, x0)
        errors = result.errors
        i = 0
        while i < restart - 1 and result.errors[-1] >= self._rel_tol:
            result = self.solve_impl(b, result.x)
            errors.append(result.errors)
            i += 1

        qt_require(errors[-1] < self._rel_tol, "could not converge")
        result.errors = errors
        return result

    def solve_impl(self, b: list, x0: list):
        bn = norm_2(b)
        if bn == 0.0:
            result = GMRESResult([0.0], b)
            return result

        x = x0 if x0 is not None else [0.0] * len(b)
        r = [i - j for i, j in zip(b, self._A(x))]

        g = norm_2(r)
        if g / bn < self._rel_tol:
            result = GMRESResult([g / bn], x)
            return result

        v = defaultdict(list)
        v[0] = [i / j for i, j in zip(r, g)]
        h = defaultdict(list)
        h[0] = [0.0] * self._max_iter
        c = [None] * (self._max_iter + 1)
        s = [None] * (self._max_iter + 1)
        z = [None] * (self._max_iter + 1)

        z[0] = g

        errors = [g / bn]

        j = 0
        while j < self._max_iter and errors[-1] >= self._rel_tol:
            h[j+1] = [0.0] * self._max_iter
            w = self._A(v[j] if self._M is None else self._M(v[j]))

            i = 0
            while i <= j:
                h[i][j] = dot_product(w, v[i])
                w = [k - g * z for k, g, z in zip(w, h[i][j], v[i])]
                i += 1
            h[j + 1][j] = norm_2(w)
            if h[j + 1][j] < sys.float_info.epsilon * sys.float_info.epsilon:
                break
            v[j+1] = [k / g for k, g in zip(w, h[j + 1][j])]

            i = 0
            while i < j:
                h0 = c[i] * h[i][j] + s[i] * h[i + 1][j]
                h1 = -s[i] * h[i][j] + c[i] * h[i + 1][j]
                h[i][j] = h0
                h[i + 1][j] = h1
                i += 1
            nu = math.sqrt(pow(h[j][j], 2) + pow(h[j + 1][j], 2))
            c[j] = h[j][j] / nu
            s[j] = h[j + 1][j] / nu
            h[j][j] = nu
            h[j + 1][j] = 0.0
            z[j + 1] = (-s[j] * z[j])
            z[j] = (c[j] * z[j])
            errors.append(abs(z[j + 1] / bn))
            j += 1

        k = len(v) - 1
        y = [0.0] * k
        y[k - 1] = z[k - 1] / h[k - 1][k - 1]

        for i in range(k - 2, -1, -1):
            y[i] = z[i] - sum(np.multiply(h[i][i + 1: k], y[i + 1: k])) / h[i][i]

        _len1 = len(v[0])
        xm = [0] * _len1

        for i in range(_len1):
            r = []
            for j in range(k):
                r.append(v[j][i])
            xm[i] = sum(np.multiply(r, y))
        xm = (x + (xm if self._M is None else self._M(xm)))
        result = GMRESResult(errors, xm)
        return result
