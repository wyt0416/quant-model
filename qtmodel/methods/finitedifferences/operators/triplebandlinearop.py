from typing import List

import numpy as np

from qtmodel.error import qt_require, qt_ensure
from qtmodel.math.array import dot_product
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.fdmlinearop import FdmLinearOp
from qtmodel.methods.finitedifferences.operators.fdmlinearoplayout import FdmLinearOpLayout


class TripleBandLinearOp(FdmLinearOp):

    def __init__(self, direction: int, mesher: FdmMesher):
        self._direction= direction
        self._i0 = [None] * mesher.layout().size()
        self._i2 = [None] * mesher.layout().size()
        self._reverse_index = [None] * mesher.layout().size()
        self._lower = [None] * mesher.layout().size()
        self._diag = [None] * mesher.layout().size()
        self._upper = [None] * mesher.layout().size()
        self._mesher = mesher

        layout = mesher.layout()
        end_iter = layout.end()

        new_dim = layout.dim()
        new_dim[self._direction], new_dim[0] = new_dim[0], new_dim[self._direction]
        new_spacing = FdmLinearOpLayout(new_dim).spacing()
        new_spacing[self._direction], new_spacing[0] = new_spacing[0], new_spacing[self._direction]

        iter = layout.begin()
        while iter!=end_iter:
            i = iter.index()

            self._i0[i] = layout.neighbourhood(iter, direction, -1)
            self._i2[i] = layout.neighbourhood(iter, direction, 1)

            coordinates = iter.coordinates()
            new_index = dot_product(coordinates, new_spacing)
            self._reverse_index[new_index] = i
            iter.increment()

    def swap(self, m):
        m._mesher, self._mesher = self._mesher, m._mesher
        m._direction, self._direction = self._direction, m._direction

        m._i0, self._i0 = self._i0, m._i0
        m._i2, self._i2 = self._i2, m._i2
        m._reverse_index, self._reverse_index = self._reverse_index, m._reverse_index
        m._lower, self._lower = self._lower, m._lower
        m._diag, self._diag = self._diag, m._diag
        m._upper, self._upper = self._upper, m._upper

    def axpyb(self, a: list, x, y, b: list):
        size = self._mesher.layout().size()

        diag = self._diag
        lower = self._lower
        upper = self._upper

        y_diag = y._diag
        y_lower = y._lower
        y_upper = y._upper

        if len(a) == 0:
            if len(b) == 0:
                # pragma omp parallel for
                i = 0
                while i < size:
                    diag[i] = y_diag[i]
                    lower[i] = y_lower[i]
                    upper[i] = y_upper[i]
                    i += 1
            else:
                bptr = b
                binc = 1 if (len(b) > 1) else 0
                # pragma omp parallel for
                i = 0
                while i < size:
                    diag[i] = y_diag[i] + bptr[i *binc]
                    lower[i] = y_lower[i]
                    upper[i] = y_upper[i]
                    i += 1
        elif len(b) == 0:
            aptr = a
            ainc = 1 if (len(a) > 1) else 0

            x_diag = x._diag
            x_lower = x._lower
            x_upper = x._upper

            ##pragma omp parallel for
            i = 0
            while i < size:
                s = aptr[i * ainc]
                diag[i] = y_diag[i] + s *x_diag[i]
                lower[i] = y_lower[i] + s *x_lower[i]
                upper[i] = y_upper[i] + s *x_upper[i]
                i += 1
        else:
            bptr = b
            binc = 1 if (len(b) > 1) else 0

            aptr = a
            ainc = 1 if (len(a) > 1) else 0

            x_diag = x._diag
            x_lower = x._lower
            x_upper = x._upper

            ##pragma omp parallel for
            i = 0
            while i < size:
                s = aptr[i * ainc]
                diag[i] = y_diag[i] + s *x_diag[i] + bptr[i *binc]
                lower[i] = y_lower[i] + s *x_lower[i]
                upper[i] = y_upper[i] + s *x_upper[i]
                i += 1

    def add(self, m = None, u: List = None):

        ret_val = TripleBandLinearOp(self._direction, self._mesher)
        size = self._mesher.layout().size()
        ##pragma omp parallel for
        i = 0
        if m is not None:
            while i < size:
                ret_val._lower[i] = self._lower[i] + m._lower[i]
                ret_val._diag[i] = self._diag[i] + m._diag[i]
                ret_val._upper[i] = self._upper[i] + m._upper[i]
                i += 1
            return ret_val

        elif u is not None:
            while i < size:
                ret_val._lower[i] = self._lower[i]
                ret_val._upper[i] = self._upper[i]
                ret_val._diag[i] = self._diag[i] + u[i]
                i += 1
            return ret_val

    def mult(self, u: list):

        ret_val = TripleBandLinearOp(self._direction, self._mesher)

        size = self._mesher.layout().size()
        # pragma omp parallel for
        i = 0
        while i < size:
            s = u[i]
            ret_val._lower[i] = self._lower[i] * s
            ret_val._diag[i] = self._diag[i] * s
            ret_val._upper[i] = self._upper[i] * s
            i += 1

        return ret_val

    def mult_r(self, u: list):
        """ interpret u as the diagonal of a diagonal matrix, multiplied on LHS """
        layout = self._mesher.layout()
        size = layout.size()
        qt_require(len(u) == size, "inconsistent size of rhs")
        ret_val = TripleBandLinearOp(self._direction, self._mesher)

        i = 0
        ##pragma omp parallel for
        while i < int(size):
            sm1 = u[i - 1] if i > 0 else 1.0
            s0 = u[i]
            sp1 = u[i + 1] if i < int(size) - 1 else 1.0
            ret_val._lower[i] = self._lower[i] * sm1
            ret_val._diag[i] = self._diag[i] * s0
            ret_val._upper[i] = self._upper[i] * sp1
            i += 1

        return ret_val

    def apply(self, r: list):
        index = self._mesher.layout()

        qt_require(len(r) == index.size(), "inconsistent length of r")

        lptr = self._lower
        dptr = self._diag
        uptr = self._upper
        i0ptr = self._i0
        i2ptr = self._i2

        ret_val = [None] * len(r)
        # pragma omp parallel for
        i = 0
        while i < index.size():
            ret_val[i] = r[i0ptr[i]] * lptr[i] + r[i] * dptr[i] + r[i2ptr[i]] * uptr[i]
            i += 1

        return ret_val

    def solve_splitting(self, r: list, a, b=1.0):
        layout = self._mesher.layout()
        qt_require(len(r) == layout.size(), "inconsistent size of rhs")

        iter = layout.begin()
        while iter != layout.end():
            coordinates = iter.coordinates()
            qt_require(coordinates[self._direction] != 0 or self._lower[iter.index()] == 0,
                       "removing non zero entry!")
            qt_require(coordinates[self._direction] is not layout.dim()[self._direction] - 1 or self._upper[
                iter.index()] == 0, "removing non zero entry!")
            iter.increment()
        ##endif

        ret_val = [None] * len(r)
        tmp = [None] * len(r)

        lptr = self._lower
        dptr = self._diag
        uptr = self._upper

        # Thomson algorithm to solve a tridiagonal system.
        # Example code taken from Tridiagonalopertor and
        # changed to fit for the triple band operator.
        rim1 = self._reverse_index[0]
        bet = 1.0 / (a * dptr[rim1] + b)
        qt_require(bet != 0.0, "division by zero")
        ret_val[self._reverse_index[0]] = r[rim1] * bet

        j = 1
        while j <= layout.size() - 1:
            ri = self._reverse_index[j]
            tmp[j] = a * uptr[rim1] * bet

            bet=b+a*(dptr[ri]-tmp[j]*lptr[ri])
            qt_ensure(bet != 0.0, "division by zero")
            bet = 1.0 / bet

            ret_val[ri] = (r[ri] - a * lptr[ri] * ret_val[rim1]) * bet
            rim1 = ri
            j += 1
        # cannot be j>=0 with Size j
        for j in range(layout.size() - 2, 0, -1):
            ret_val[self._reverse_index[j]] -= tmp[j + 1] * ret_val[self._reverse_index[j + 1]]
        ret_val[self._reverse_index[0]] -= tmp[1] * ret_val[self._reverse_index[1]]

        return ret_val

    def to_matrix(self):
        index = self._mesher.layout()
        n = index.size()

        ret_val = np.zeros((n*n))
        i = 0
        while i < n:
            ret_val[i, self._i0[i]] += self._lower[i]
            ret_val[i, i] += self._diag[i]
            ret_val[i, self._i2[i]] += self._upper[i]
            i += 1

        return ret_val

