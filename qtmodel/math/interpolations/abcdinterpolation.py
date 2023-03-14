import sys

from qtmodel.error import qt_require, QTError
from qtmodel.math.abcdmathfunction import AbcdMathFunction
from qtmodel.math.interpolation import InterpolationTemplateImpl, Interpolation
from qtmodel.math.interpolations.linearinterpolation import LinearInterpolation
from qtmodel.math.optimization.endcriteria import EndCriteriaTypes, EndCriteria
from qtmodel.math.optimization.method import OptimizationMethod
from qtmodel.termstructures.volatility.abcdcalibration import AbcdCalibration
from qtmodel.types import Real


class AbcdCoeffHolder:

    def __init__(self,
                 a: Real,
                 b: Real,
                 c: Real,
                 d: Real,
                 a_is_fixed: bool,
                 b_is_fixed: bool,
                 c_is_fixed: bool,
                 d_is_fixed: bool):
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._a_is_fixed = False
        self._b_is_fixed = False
        self._c_is_fixed = False
        self._d_is_fixed = False
        self._k = []
        self._error = sys.float_info.max
        self._max_error = sys.float_info.max
        self._abcd_end_criteria = EndCriteriaTypes.Null

        if self._a != sys.float_info.max:
            self._a_is_fixed = a_is_fixed
        else:
            self._a = -0.06
        if self._b != sys.float_info.max:
            self._b_is_fixed = b_is_fixed
        else:
            self._b = 0.17
        if self._c != sys.float_info.max:
            self._c_is_fixed = c_is_fixed
        else:
            self._c = 0.54
        if self._d != sys.float_info.max:
            self._d_is_fixed = d_is_fixed
        else:
            self._d = 0.17

        AbcdMathFunction.validate(a, b, c, d)


class AbcdInterpolationImpl(InterpolationTemplateImpl, AbcdCoeffHolder):

    def __init__(self,
                 x: list,
                 y: list,
                 a: Real,
                 b: Real,
                 c: Real,
                 d: Real,
                 a_is_fixed: bool,
                 b_is_fixed: bool,
                 c_is_fixed: bool,
                 d_is_fixed: bool,
                 vega_weighted: bool,
                 end_criteria: EndCriteria,
                 opt_method: OptimizationMethod):
        InterpolationTemplateImpl.__init__(self, x, y)
        AbcdCoeffHolder(a, b, c, d, a_is_fixed, b_is_fixed, c_is_fixed, d_is_fixed)
        self._end_criteria = end_criteria
        self._opt_method = opt_method
        self._vega_weighted = vega_weighted
        self._abcd_calibrator = None

    def update(self):
        x = self._x
        y = self._y
        times = list(x)
        black_vols = list(y)

        self._abcd_calibrator = AbcdCalibration(times,
                                                black_vols,
                                                self._a,
                                                self._b,
                                                self._c,
                                                self._d,
                                                self._a_is_fixed,
                                                self._b_is_fixed,
                                                self._c_is_fixed,
                                                self._d_is_fixed,
                                                self._vega_weighted,
                                                self._end_criteria,
                                                self._opt_method)
        self._abcd_calibrator.compute()
        self._a = self._abcd_calibrator.a()
        self._b = self._abcd_calibrator.b()
        self._c = self._abcd_calibrator.c()
        self._d = self._abcd_calibrator.d()
        self._k = self._abcd_calibrator.k(times, black_vols)
        self._error = self._abcd_calibrator.error()
        self._max_error = self._abcd_calibrator.max_error()
        self._abcd_end_criteria = self._abcd_calibrator.end_criteria()

    def value(self, x: Real):
        qt_require(x >= 0.0, f"time must be non negative: {x} not allowed")
        return self._abcd_calibrator.value(x)

    def primitive(self, x: Real):
        QTError("Abcd primitive not implemented")

    def derivative(self, x: Real):
        QTError("Abcd derivative not implemented")

    def second_derivative(self, x: Real):
        QTError("Abcd secondDerivative not implemented")

    def k(self, t: Real):
        li = LinearInterpolation(self._x, self._y)
        return li(t)


class AbcdInterpolation(Interpolation):
    """
    Abcd interpolation between discrete points.
    See the Interpolation class for information about the required lifetime of the underlying data.
    """

    def __init__(self,
                 x: list,  # x = times
                 y: list,  # y = volatilities
                 a: Real = -0.06,
                 b: Real = 0.17,
                 c: Real = 0.54,
                 d: Real = 0.17,
                 a_is_fixed: bool = False,
                 b_is_fixed: bool = False,
                 c_is_fixed: bool = False,
                 d_is_fixed: bool = False,
                 vega_weighted: bool = False,
                 end_criteria: EndCriteria = None,
                 opt_method: OptimizationMethod = None):
        super(AbcdInterpolation, self).__init__()
        self._impl = AbcdInterpolationImpl(x, y,
                                           a, b, c, d,
                                           a_is_fixed, b_is_fixed,
                                           c_is_fixed, d_is_fixed,
                                           vega_weighted,
                                           end_criteria,
                                           opt_method)
        self._impl.update()
        self._coeffs = self._impl

    def a(self):
        return self._coeffs._a

    def b(self):
        return self._coeffs._b

    def c(self):
        return self._coeffs._c

    def d(self):
        return self._coeffs._d

    def rmsError(self):
        return self._coeffs._error

    def maxError(self):
        return self._coeffs._max_error

    def endCriteria(self):
        return self._coeffs._abcd_end_criteria

    def k(self, t: Real = None, x: list = None):
        if t is not None and x is not None:
            li = LinearInterpolation(x, self._coeffs._k)
            return li(t)
        else:
            return self._coeffs._k


class Abcd:
    """ interpolation factory and traits """

    global_ = True

    def __init__(self,
                 a: Real,
                 b: Real,
                 c: Real,
                 d: Real,
                 a_is_fixed: bool,
                 b_is_fixed: bool,
                 c_is_fixed: bool,
                 d_is_fixed: bool,
                 vega_weighted: bool = False,
                 end_criteria: EndCriteria = None,
                 opt_method: OptimizationMethod = None):
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._a_is_fixed = a_is_fixed
        self._b_is_fixed = b_is_fixed
        self._c_is_fixed = c_is_fixed
        self._d_is_fixed = d_is_fixed
        self._vega_weighted = vega_weighted
        self._end_criteria = end_criteria
        self._opt_method = opt_method

    def interpolate(self, x: list, y: list):
        return AbcdInterpolation(x, y,
                                 self._a, self._b, self._c, self._d,
                                 self._a_is_fixed, self._b_is_fixed,
                                 self._c_is_fixed, self._d_is_fixed,
                                 self._vega_weighted,
                                 self._end_criteria, self._opt_method)
