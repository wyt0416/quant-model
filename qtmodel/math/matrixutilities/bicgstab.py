from typing import List, Callable

from qtmodel.error import qt_require
from qtmodel.math.array import norm_2, dot_product
from qtmodel.types import Real


class BiCGStabResult:

    def __init__(self, iterations: int, error: Real, x: List):
        self.iterations = iterations
        self.error = error
        self.x = x


class BiCGstab:

    def __init__(self,
                 A: Callable[[list], list],
                 max_iter: int,
                 rel_tol: Real,
                 pre_conditioner: Callable[[list], list] = None):

        self._A = A
        self._M = pre_conditioner
        self._max_iter = max_iter
        self._rel_tol = rel_tol

    def solve(self, b: List, x0: List = None):
        bnorm2 = norm_2(b)
        if bnorm2 == 0.0:
            result = BiCGStabResult(0, 0.0, b)
            return result

        x = x0 if x0 is not None else [0.0] * len(b)
        r = [i - j for i, j in zip(b, self._A(x))]

        r_tld = r
        p = None
        v = None
        omega = 1.0
        rho_tld = 1.0
        alpha = 0.0
        error = norm_2(r) / bnorm2

        i = 0
        while i < self._max_iter and error >= self._rel_tol:
            rho = dot_product(r_tld, r)
            if rho == 0.0 or omega == 0.0:
                break

            if i != 0:
                beta = (rho / rho_tld) * (alpha / omega)
                p = [i + beta * (j - omega * z) for i, j, z in zip(r, p, v)]
            else:
                p = r

            p_tld = p if self._M is None else self._M(p)
            v = self._A(p_tld)

            alpha = rho / dot_product(r_tld, v)
            s = [i - alpha * j for i, j in zip(r, v)]
            if norm_2(s) < self._rel_tol * bnorm2:
                x += [i + alpha * j for i, j in zip(x, p_tld)]
                error = norm_2(s) / bnorm2
                break

            s_tld = s if self._M is None else self._M(s)
            t = self._A(s_tld)
            omega = dot_product(t, s) / dot_product(t, t)
            x = [alpha * i + omega * j + z for i, j, z in zip(p_tld, s_tld, x)]
            r = [i - omega * j for i, j in zip(s, t)]
            error = norm_2(r) / bnorm2
            rho_tld = rho
            i += 1

        qt_require(i < self._max_iter, "max number of iterations exceeded")
        qt_require(error < self._rel_tol, "could not converge")

        result = BiCGStabResult(i, error, x)
        return result
