import math
import sys

from scipy.stats import norm

from qtmodel.error import qt_require, QTError
from qtmodel.math.comparison import close_enough
from qtmodel.math.errorfunction import ErrorFunction
from qtmodel.mathconstants import M_SQRT_2, M_1_SQRTPI, M_SQRTPI


class NormalDistribution:
    """
    Normal distribution function
    Given x, it returns its probability in a Gaussian normal distribution.
    It provides the first derivative too.
    """

    def __init__(self, average=0.0, sigma=1.0):
        qt_require(sigma > 0, f"sigma must be greater than 0.0 ({sigma} not allowed)")
        self._average = average
        self._sigma = sigma

        self._normalization_factor = M_SQRT_2 * M_1_SQRTPI / self._sigma
        self._der_normalization_factor = self._sigma * self._sigma
        self._denominator = 2.0 * self._der_normalization_factor

    def __call__(self, x):
        deltax = x - self._average
        exponent = -(deltax * deltax) / self._denominator
        # debian alpha had some strange problem in the very-low range
        return 0.0 if exponent <= -690.0 else self._normalization_factor * math.exp(
            exponent)  # exp(x) < 1.0e-300 anyway

    def derivative(self, x):
        return (self(x) * (self._average - x)) / self._der_normalization_factor


class CumulativeNormalDistribution:
    """
    Cumulative normal distribution function
    Given x it provides an approximation to the integral of the gaussian
    normal distribution: formula here ...
    For this implementation see M. Abramowitz and I. Stegun, Handbook of
    Mathematical Functions, Dover Publications, New York (1972)
    """

    def __init__(self, average=0.0, sigma=1.0):
        qt_require(sigma > 0.0, f"sigma must be greater than 0.0 ({sigma} not allowed)")
        self._average = average
        self._sigma = sigma
        self._gaussian = NormalDistribution()
        self._error_function = ErrorFunction()

    def __call__(self, z):

        z = (z - self._average) / self._sigma

        result = 0.5 * (1.0 + self._error_function(z * M_SQRT_2))
        if result <= 1e-8:  # todo: investigate the threshold level
            # Asymptotic expansion for very negative x following (26.2.12)
            # on page 408 in M. Abramowitz and A. Stegun,
            # Pocketbook of Mathematical Functions, ISBN 3-87144818-4.
            sum_ = 1.0
            zsqr = z * z
            i = 1.0
            g = 1.0
            a = sys.float_info.max
            while 1:
                lasta = a
                x = (4.0 * i - 3.0) / zsqr
                y = x * ((4.0 * i - 1) / zsqr)
                a = g * (x - y)
                sum_ -= a
                g *= y
                i += 1
                a = abs(a)
                if not (lasta > a >= abs(sum_ * sys.float_info.epsilon)):
                    break
            result = -self._gaussian(z) / z * sum_

        return result

    def derivative(self, x):
        xn = (x - self._average) / self._sigma
        return self._gaussian(xn) / self._sigma


class InverseCumulativeNormal:
    """
    Inverse cumulative normal distribution function
    Given x between zero and one as the integral value of a gaussian
    normal distribution this class provides the value y such that
    formula here ...

    It use Acklam's approximation:
    by Peter J. Acklam, University of Oslo, Statistics Division.
    URL: http://home.online.no/~pjacklam/notes/invnorm/index.html

    This class can also be used to generate a gaussian normal
    distribution from a uniform distribution.
    This is especially useful when a gaussian normal distribution
    is generated from a low discrepancy uniform distribution:
    in this case the traditional Box-Muller approach and its
    variants would not preserve the sequence's low-discrepancy.
    """

    # Coefficients for the rational approximation.
    _a1 = -3.969683028665376e+01
    _a2 = 2.209460984245205e+02
    _a3 = -2.759285104469687e+02
    _a4 = 1.383577518672690e+02
    _a5 = -3.066479806614716e+01
    _a6 = 2.506628277459239e+00

    _b1 = -5.447609879822406e+01
    _b2 = 1.615858368580409e+02
    _b3 = -1.556989798598866e+02
    _b4 = 6.680131188771972e+01
    _b5 = -1.328068155288572e+01

    _c1 = -7.784894002430293e-03
    _c2 = -3.223964580411365e-01
    _c3 = -2.400758277161838e+00
    _c4 = -2.549732539343734e+00
    _c5 = 4.374664141464968e+00
    _c6 = 2.938163982698783e+00

    _d1 = 7.784695709041462e-03
    _d2 = 3.224671290700398e-01
    _d3 = 2.445134137142996e+00
    _d4 = 3.754408661907416e+00

    # Limits of the approximation regions
    _x_low = 0.02425
    _x_high = 1.0 - _x_low

    _f = CumulativeNormalDistribution()

    def __init__(self, average=0.0, sigma=1.0):
        qt_require(sigma > 0.0, f"sigma must be greater than 0.0 ({sigma} not allowed)")
        self._average = average
        self._sigma = sigma

    def __call__(self, x):
        return self._average + self._sigma * self.standard_value(x)

    def standard_value(self, x):

        if x < self._x_low or self._x_high < x:
            z = self.tail_value(x)
        else:
            z = x - 0.5
            r = z * z
            z = (((((self._a1 * r + self._a2) * r + self._a3) * r + self._a4) * r + self._a5) * r + self._a6) * z / (
                    ((((self._b1 * r + self._b2) * r + self._b3) * r + self._b4) * r + self._b5) * r + 1.0)

        # The relative error of the approximation has absolute value less
        # than 1.15e-9.  One iteration of Halley's rational method (third
        # order) gives full machine precision.
        r = (self._f(z) - x) * math.sqrt(2) * M_SQRTPI * math.exp(0.5 * z * z)
        # Halley's method
        z -= r / (1 + 0.5 * z * r)

        return z

    def tail_value(self, x):
        if x <= 0.0 or x >= 1.0:
            # try to recover if due to numerical error
            if close_enough(x, 1.0):
                return sys.float_info.max  # largest value available
            elif abs(x) < sys.float_info.epsilon:
                return sys.float_info.min  # largest negative value available
            else:
                QTError(f"InverseCumulativeNormal({x}) undefined: must be 0 < x < 1")

        if x < self._x_low:
            # Rational approximation for the lower region 0<x<u_low
            z = math.sqrt(-2.0 * math.log(x))
            z = (((((self._c1 * z + self._c2) * z + self._c3) * z + self._c4) * z + self._c5) * z + self._c6) / (
                    (((self._d1 * z + self._d2) * z + self._d3) * z + self._d4) * z + 1.0)

        else:
            # Rational approximation for the upper region_ uhigh<x<1
            z = math.sqrt(-2.0 * math.log(1.0 - x))
            z = -(((((self._c1 * z + self._c2) * z + self._c3) * z + self._c4) * z + self._c5) * z + self._c6) / (
                    (((self._d1 * z + self._d2) * z + self._d3) * z + self._d4) * z + 1.0)

        return z


class MoroInverseCumulativeNormal:
    """
    Moro Inverse cumulative normal distribution class
    Given x between zero and one as the integral value of a gaussian normal
    distribution this class provides the value y such that formula here ...
    It uses Beasly and Springer approximation, with an improved approximation
    for the tails. See Boris Moro, "The Full Monte", 1995, Risk Magazine.
    This class can also be used to generate a gaussian normal distribution
    from a uniform distribution.
    This is especially useful when a gaussian normal distribution is generated
    from a low discrepancy uniform distribution: in this case the traditional
    Box-Muller approach and its variants would not preserve the sequence's
    low-discrepancy.
    """
    _a0 = 2.50662823884
    _a1 = -18.61500062529
    _a2 = 41.39119773534
    _a3 = -25.44106049637

    _b0 = -8.47351093090
    _b1 = 23.08336743743
    _b2 = -21.06224101826
    _b3 = 3.13082909833

    _c0 = 0.3374754822726147
    _c1 = 0.9761690190917186
    _c2 = 0.1607979714918209
    _c3 = 0.0276438810333863
    _c4 = 0.0038405729373609
    _c5 = 0.0003951896511919
    _c6 = 0.0000321767881768
    _c7 = 0.0000002888167364
    _c8 = 0.0000003960315187

    def __init__(self, average=0.0, sigma=1.0):
        qt_require(sigma > 0.0, f"sigma must be greater than 0.0 ({sigma} not allowed)")
        self._average = average
        self._sigma = sigma

    def __call__(self, x):
        qt_require(0.0 < x < 1.0,
                   f"MoroInverseCumulativeNormal({x}) undefined: must be 0<x<1")

        temp = x - 0.5

        if abs(temp) < 0.42:
            # Beasley and Springer, 1977
            result = temp * temp
            result = temp * (((self._a3 * result + self._a2) * result + self._a1) * result + self._a0) / (
                    (((self._b3 * result + self._b2) * result + self._b1) * result + self._b0) * result + 1.0)

        else:
            # improved approximation for the tail (Moro 1995)
            if x < 0.5:
                result = x
            else:
                result = 1.0 - x
            result = math.log(-math.log(result))
            result = self._c0 + result * (self._c1 + result * (self._c2 + result * (self._c3 + result * (
                    self._c4 + result * (
                    self._c5 + result * (self._c6 + result * (self._c7 + result * self._c8)))))))
            if x < 0.5:
                result = -result

        return self._average + result * self._sigma


class MaddockInverseCumulativeNormal:
    """
    Maddock's Inverse cumulative normal distribution class
    Given x between zero and one as the integral value of a gaussian normal
    distribution this class provides the value y such that formula here ...
    From the boost documentation:
    These functions use a rational approximation devised by  John Maddock to
    calculate an initial approximation to the result that is accurate to ~10^-19,
    then only if that has insufficient accuracy compared to the epsilon for
    type double, do we clean up the result using Halley iteration.
    """

    def __init__(self, average=0.0, sigma=1.0):
        self._average = average
        self._sigma = sigma

    def __call__(self, x):
        return norm.ppf(q=x, loc=self._average, scale=self._sigma)


class MaddockCumulativeNormal:
    """ Maddock's cumulative normal distribution class """
    def __init__(self, average=0.0, sigma=1.0):
        self._average = average
        self._sigma = sigma

    def __call__(self, x):
        return norm.cdf(x=x, loc=self._average, scale=self._sigma)
