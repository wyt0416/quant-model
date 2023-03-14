# Copyright (C) 2003, 2004 Ferdinando Ametrano
# Copyright (C) 2003 StatPro Italia srl
# Copyright (C) 2005 Gary Kennedy
# Copyright (C) 2013 Fabien Le Floc'h
# Copyright (C) 2016 Klaus Spanderen

from typing import Callable
import numpy as np

from qtmodel.math.comparison import close
from qtmodel.math.distributions.bivariatestudenttdistribution import *
from qtmodel.math.distributions.normaldistribution import *
from qtmodel.math.distributions.bivariatenormaldistribution import *
from qtmodel.math.distributions.chisquaredistribution import *
from qtmodel.math.distributions.gammadistribution import *
from qtmodel.math.distributions.binomialdistribution import *
from qtmodel.math.distributions.poissondistribution import *
from qtmodel.math.randomnumbers.stochasticcollocationinvcdf import StochasticCollocationInvCDF
from utilities import norm_test

average = 1.0
sigma = 2.0


class InverseNonCentralChiSquared:
    def __init__(self, df: float, ncp: float):
        self._df = df
        self._ncp = ncp
        self.dist = np.random.noncentral_chisquare(self._df, self._ncp, size=None)

    def __call__(self, x):
        return np.quantile(self.dist, x)


values = [[0.0, 0.0, 0.0, 0.250000],
          [0.0, 0.0, -0.5, 0.166667],
          [0.0, 0.0, 0.5, 1.0 / 3],
          [0.0, -0.5, 0.0, 0.154269],
          [0.0, -0.5, -0.5, 0.081660],
          [0.0, -0.5, 0.5, 0.226878],
          [0.0, 0.5, 0.0, 0.345731],
          [0.0, 0.5, -0.5, 0.273122],
          [0.0, 0.5, 0.5, 0.418340],

          [-0.5, 0.0, 0.0, 0.154269],
          [-0.5, 0.0, -0.5, 0.081660],
          [-0.5, 0.0, 0.5, 0.226878],
          [-0.5, -0.5, 0.0, 0.095195],
          [-0.5, -0.5, -0.5, 0.036298],
          [-0.5, -0.5, 0.5, 0.163319],
          [-0.5, 0.5, 0.0, 0.213342],
          [-0.5, 0.5, -0.5, 0.145218],
          [-0.5, 0.5, 0.5, 0.272239],

          [0.5, 0.0, 0.0, 0.345731],
          [0.5, 0.0, -0.5, 0.273122],
          [0.5, 0.0, 0.5, 0.418340],
          [0.5, -0.5, 0.0, 0.213342],
          [0.5, -0.5, -0.5, 0.145218],
          [0.5, -0.5, 0.5, 0.272239],
          [0.5, 0.5, 0.0, 0.478120],
          [0.5, 0.5, -0.5, 0.419223],
          [0.5, 0.5, 0.5, 0.546244],

          # known analytical values
          [0.0, 0.0, math.sqrt(1 / 2.0), 3.0 / 8],

          # [  0.0,  big,  any, 0.500000 ],
          [0.0, 30, -1.0, 0.500000],
          [0.0, 30, 0.0, 0.500000],
          [0.0, 30, 1.0, 0.500000],

          # [ big,  big,   any, 1.000000 ],
          [30, 30, -1.0, 1.000000],
          [30, 30, 0.0, 1.000000],
          [30, 30, 1.0, 1.000000],

          # [-big,  any,   any, 0.000000 ]
          [-30, -1.0, -1.0, 0.000000],
          [-30, 0.0, -1.0, 0.000000],
          [-30, 1.0, -1.0, 0.000000],
          [-30, -1.0, 0.0, 0.000000],
          [-30, 0.0, 0.0, 0.000000],
          [-30, 1.0, 0.0, 0.000000],
          [-30, -1.0, 1.0, 0.000000],
          [-30, 0.0, 1.0, 0.000000],
          [-30, 1.0, 1.0, 0.000000]]


def gaussian(x):
    norm_fact = sigma * math.sqrt(2 * math.pi)
    dx = x - average
    return math.exp(-dx * dx / (2.0 * sigma * sigma)) / norm_fact


def gaussian_derivative(x):
    norm_fact = sigma * sigma * sigma * math.sqrt(2 * math.pi)
    dx = x - average
    return -dx * math.exp(-dx * dx / (2.0 * sigma * sigma)) / norm_fact


def check_bivariate(f: Callable[[float], object],
                    tag: str):
    i = 0
    while i < len(values):
        bcd = f(values[i][2])
        value = bcd(values[i][0], values[i][1])

        tolerance = 1.0e-6
        if abs(value - values[i][3]) >= tolerance:
            raise QTError(
                f"{tag} bivariate cumulative distribution\n case:{i + 1} \n a: {values[i][0]} \n b: {values[i][1]}\n"
                f" rho: {values[i][2]} \n tabulated value: {values[i][3]} \n result: {value}")
        i += 1


def check_bivariate_at_zero(f: Callable[[float], object],
                            tag: str,
                            tolerance: float):
    '''
    BVN(0.0,0.0,rho) = 1/4 + arcsin(rho)/(2*M_PI)
              "Handbook of the Normal Distribution",
              J.K. Patel & C.B.Read, 2nd Ed, 1996
    '''

    rho = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.99999]
    x = 0.0
    y = 0.0

    for i in rho:
        for sgn in range(-1, 1, 2):
            bvn = f(sgn * i)
            expected = 0.25 + math.asin(sgn * i) / (2 * math.pi)
            realised = bvn(x, y)
            if abs(realised - expected) >= tolerance:
                raise QTError(f"{tag} bivariate cumulative distribution\n rho:{sgn * i} \n expected: {expected}\n"
                              f"realised:{realised} \n tolerance: {tolerance}")


def check_bivariate_tail(f: Callable[[float], object],
                         tag: str,
                         tolerance: float):
    '''
             make sure numerical greeks are sensible, numerical error in
             * the tails can make garbage greeks for partial time barrier
             * option
    '''
    x = -6.9
    y = 6.9
    corr = -0.999
    bvn = f(corr)
    for i in range(0, 9):
        cdf0 = bvn(x, y)
        y = y + tolerance
        cdf1 = bvn(x, y)
        if cdf0 > cdf1:
            raise QTError(
                f"{tag} cdf must be decreasing in the tails\n cdf0: {cdf0} \n cdf1: {cdf1} \n x: {x} \n y: {y} \n "
                f"rho: {corr}")


def test_normal():
    print("Testing normal distributions...")

    inv_cum_standard_normal = InverseCumulativeNormal()
    check = inv_cum_standard_normal(0.5)
    if check != 0.0:
        raise QTError(f"C++ inverse cumulative of the standard normal at 0.5 is {check} \n instead of zero:"
                      f" something is wrong!")

    normal = NormalDistribution(average, sigma)
    cum = CumulativeNormalDistribution(average, sigma)
    inv_cum = InverseCumulativeNormal(average, sigma)

    number_of_standard_deviation = 6
    x_min = average - number_of_standard_deviation * sigma
    x_max = average + number_of_standard_deviation * sigma
    n = 100001
    h = (x_max - x_min) / (n - 1)

    x = [None] * n
    y = [None] * n
    yd = [None] * n
    temp = [None] * n
    diff = [None] * n

    i = 0
    while i < n:
        x[i] = (x_min + h * i)
        i += 1
    y = list(map(gaussian, x))
    yd = list(map(gaussian_derivative, x))

    # check that normal = Gaussian
    temp = list(map(normal, x))
    diff = list([y[i] - temp[i] for i in range(len(y))])
    e = norm_test(diff, h)

    if e > 1.0e-16:
        raise QTError(
            f"norm of NormalDistribution minus analytic Gaussian: {e}\n tolerance exceeded")

    # check that invCum . cum = identity
    temp = list(map(cum, x))
    temp = list(map(inv_cum, temp))
    diff = list([x[i] - temp[i] for i in range(len(y))])
    e = norm_test(diff, h)

    if e > 1.0e-7:
        raise QTError(
            f"norm of inv_cum . cum minus identity: {e}\n tolerance exceeded")

    m_inv_cum = MaddockInverseCumulativeNormal(average, sigma)
    diff = list(map(lambda i: i - m_inv_cum(cum(i)), x))
    e = norm_test(diff, h)

    if e > 1.0e-7:
        raise QTError(
            f"norm of MaddokInvCum . cum minus identity: {e}\n tolerance exceeded")

    # check that cum.derivative = Gaussian
    i = 0
    while i < len(x):
        temp[i] = cum.derivative(x[i])
        i += 1
    diff = list([y[i] - temp[i] for i in range(len(y))])
    e = norm_test(diff, h)

    if e > 1.0e-16:
        raise QTError(
            f"norm of C++ Cumulative.derivative minus analytic Gaussian: {e}\ntolerance exceeded")

    # check that normal.derivative = gaussianDerivative
    i = 0
    while i < len(x):
        temp[i] = normal.derivative(x[i])
        i += 1
    diff = list([yd[i] - temp[i] for i in range(len(yd))])
    e = norm_test(diff, h)

    if e > 1.0e-16:
        raise QTError(
            f"norm of normal derivative minus analytic derivative: {e}\n tolerance exceeded")


def test_bivariate():
    print("Testing bivariate cumulative normal distribution...")

    check_bivariate_at_zero(BivariateCumulativeNormalDistributionDr78, "Drezner 1978", 1.0e-6)

    check_bivariate(BivariateCumulativeNormalDistributionDr78, "Drezner 1978")

    # due to relative low accuracy of Dr78, it does not pass with a smaller perturbation
    check_bivariate_tail(BivariateCumulativeNormalDistributionDr78, "Drezner 1978", 1.0e-5)

    check_bivariate_at_zero(BivariateCumulativeNormalDistributionWe04DP, "West 2004", 1.0e-15)

    check_bivariate(BivariateCumulativeNormalDistributionWe04DP, "West 2004")

    check_bivariate_tail(BivariateCumulativeNormalDistributionWe04DP, "West 2004", 1.0e-6)

    check_bivariate_tail(BivariateCumulativeNormalDistributionWe04DP, "West 2004", 1.0e-8)


def test_poisson():
    print("Testing Poisson distribution...")
    mean = 0
    while mean <= 10:
        i = 0
        pdf = PoissonDistribution(mean)
        calculated = pdf(i)
        log_helper = -mean
        expected = math.exp(log_helper)
        error = abs(calculated - expected)
        if error > 1.0e-16:
            raise QTError(
                f"Poisson pdf([mean] )([i])\n calculated: [calculated] \n expected: [expected]\n error: [error]")

        for i in range(1, 24):
            calculated = pdf(i)
            if mean == 0.0:
                expected = 0.0
            else:
                log_helper = log_helper + math.log(mean) - math.log(i)
                expected = math.exp(log_helper)
            error = abs(calculated - expected)
            if error > 1.0e-13:
                raise QTError(
                    f"Poisson pdf([mean])([i])\n calculated:  [calculated] \n expected: [expected]\n error: [error]")
        mean += 0.5


def test_cumulative_poisson():
    print("Testing cumulative Poisson distribution...")
    mean = 0
    while mean <= 10:
        i = 0
        cdf = CumulativePoissonDistribution(mean)
        cum_calculated = cdf(i)
        log_helper = -mean
        cum_expected = math.exp(log_helper)
        error = abs(cum_calculated - cum_expected)
        if error > 1.0e-13:
            raise QTError(
                f"Poisson cdf([mean])([i])\n calculated: [cum_calculated] \n expected: [cum_expected]\n error: [error]")
        for i in range(1, 24):
            cum_calculated = cdf(i)
            if mean == 0.0:
                cum_expected = 1.0
            else:
                log_helper = log_helper + math.log(mean) - math.log(i)
                cum_expected += math.exp(log_helper)
            error = abs(cum_calculated - cum_expected)
            if error > 1.0e-12:
                raise QTError(
                    f"Poisson cdf([mean])([i])\n calculated: [cum_calculated] \n expected: [cum_expected]\n error: [error]")
        mean += 0.5


def testInverseCumulativePoisson():
    print("Testing inverse cumulative Poisson distribution...")

    icp = InverseCumulativePoisson(1.0)

    data = [0.2, 0.5, 0.9, 0.98, 0.99, 0.999, 0.9999, 0.99995, 0.99999, 0.999999, 0.9999999, 0.99999999]

    i = 0
    while i < len(data):
        if not close(icp(data[i]), i):
            print(f"failed to reproduce known value for x = [data[i]] \n calculated: [icp(data[i])] \n expected: [i]")
        i += 1


def test_bivariate_cumulative_student():
    print("Testing bivariate cumulative Student t distribution...")
    xs = [0.00, 0.50, 1.00, 1.50, 2.00, 2.50, 3.00, 4.00, 5.00, 6.00, 7.00, 8.00, 9.00, 10.00]
    ns = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 60, 90, 120, 150, 300, 600]
    # Part of table 1 from the reference paper
    expected1 = [0.33333, 0.50000, 0.63497, 0.72338, 0.78063, 0.81943, 0.84704, 0.88332, 0.90590, 0.92124, 0.93231,
                 0.94066, 0.94719, 0.95243, 0.33333, 0.52017, 0.68114, 0.78925, 0.85607, 0.89754, 0.92417, 0.95433,
                 0.96978, 0.97862, 0.98411, 0.98774, 0.99026, 0.99208, 0.33333, 0.52818, 0.70018, 0.81702, 0.88720,
                 0.92812, 0.95238, 0.97667, 0.98712, 0.99222, 0.99497, 0.99657, 0.99756, 0.99821, 0.33333, 0.53245,
                 0.71052, 0.83231, 0.90402, 0.94394, 0.96612, 0.98616, 0.99353, 0.99664, 0.99810, 0.99885, 0.99927,
                 0.99951, 0.33333, 0.53510, 0.71701, 0.84196, 0.91449, 0.95344, 0.97397, 0.99095, 0.99637, 0.99836,
                 0.99918, 0.99956, 0.99975, 0.99985, 0.33333, 0.53689, 0.72146, 0.84862, 0.92163, 0.95972, 0.97893,
                 0.99365, 0.99779, 0.99913, 0.99962, 0.99982, 0.99990, 0.99995, 0.33333, 0.53819, 0.72470, 0.85348,
                 0.92679, 0.96415, 0.98230, 0.99531, 0.99857, 0.99950, 0.99981, 0.99992, 0.99996, 0.99998, 0.33333,
                 0.53917, 0.72716, 0.85719, 0.93070, 0.96743, 0.98470, 0.99639, 0.99903, 0.99970, 0.99990, 0.99996,
                 0.99998, 0.99999, 0.33333, 0.53994, 0.72909, 0.86011, 0.93375, 0.96995, 0.98650, 0.99713, 0.99931,
                 0.99981, 0.99994, 0.99998, 0.99999, 1.00000, 0.33333, 0.54056, 0.73065, 0.86247, 0.93621, 0.97194,
                 0.98788, 0.99766, 0.99950, 0.99988, 0.99996, 0.99999, 1.00000, 1.00000, 0.33333, 0.54243, 0.73540,
                 0.86968, 0.94362, 0.97774, 0.99168, 0.99890, 0.99985, 0.99998, 1.00000, 1.00000, 1.00000, 1.00000,
                 0.33333, 0.54338, 0.73781, 0.87336, 0.94735, 0.98053, 0.99337, 0.99932, 0.99993, 0.99999, 1.00000,
                 1.00000, 1.00000, 1.00000, 0.33333, 0.54395, 0.73927, 0.87560, 0.94959, 0.98216, 0.99430, 0.99952,
                 0.99996, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.33333, 0.54433, 0.74025, 0.87709, 0.95108,
                 0.98322, 0.99489, 0.99963, 0.99998, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.33333, 0.54528,
                 0.74271, 0.88087, 0.95482, 0.98580, 0.99623, 0.99983, 0.99999, 1.00000, 1.00000, 1.00000, 1.00000,
                 1.00000, 0.33333, 0.54560, 0.74354, 0.88215, 0.95607, 0.98663, 0.99664, 0.99987, 1.00000, 1.00000,
                 1.00000, 1.00000, 1.00000, 1.00000, 0.33333, 0.54576, 0.74396, 0.88279, 0.95669, 0.98704, 0.99683,
                 0.99989, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.33333, 0.54586, 0.74420, 0.88317,
                 0.95706, 0.98729, 0.99695, 0.99990, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.33333,
                 0.54605, 0.74470, 0.88394, 0.95781, 0.98777, 0.99717, 0.99992, 1.00000, 1.00000, 1.00000, 1.00000,
                 1.00000, 1.00000, 0.33333, 0.54615, 0.74495, 0.88432, 0.95818, 0.98801, 0.99728, 0.99993, 1.00000,
                 1.00000, 1.00000, 1.00000, 1.00000, 1.00000]
    # Part of table 2 from the reference paper
    expected2 = [0.16667, 0.36554, 0.54022, 0.65333, 0.72582, 0.77465, 0.80928, 0.85466, 0.88284, 0.90196, 0.91575,
                 0.92616, 0.93429, 0.94081, 0.16667, 0.38889, 0.59968, 0.73892, 0.82320, 0.87479, 0.90763, 0.94458,
                 0.96339, 0.97412, 0.98078, 0.98518, 0.98823, 0.99044, 0.16667, 0.39817, 0.62478, 0.77566, 0.86365,
                 0.91391, 0.94330, 0.97241, 0.98483, 0.99086, 0.99410, 0.99598, 0.99714, 0.99790, 0.16667, 0.40313,
                 0.63863, 0.79605, 0.88547, 0.93396, 0.96043, 0.98400, 0.99256, 0.99614, 0.99782, 0.99868, 0.99916,
                 0.99944, 0.16667, 0.40620, 0.64740, 0.80900, 0.89902, 0.94588, 0.97007, 0.98972, 0.99591, 0.99816,
                 0.99909, 0.99951, 0.99972, 0.99983, 0.16667, 0.40829, 0.65345, 0.81794, 0.90820, 0.95368, 0.97607,
                 0.99290, 0.99755, 0.99904, 0.99958, 0.99980, 0.99989, 0.99994, 0.16667, 0.40980, 0.65788, 0.82449,
                 0.91482, 0.95914, 0.98010, 0.99482, 0.99844, 0.99946, 0.99979, 0.99991, 0.99996, 0.99998, 0.16667,
                 0.41095, 0.66126, 0.82948, 0.91981, 0.96314, 0.98295, 0.99605, 0.99895, 0.99968, 0.99989, 0.99996,
                 0.99998, 0.99999, 0.16667, 0.41185, 0.66393, 0.83342, 0.92369, 0.96619, 0.98506, 0.99689, 0.99926,
                 0.99980, 0.99994, 0.99998, 0.99999, 1.00000, 0.16667, 0.41257, 0.66608, 0.83661, 0.92681, 0.96859,
                 0.98667, 0.99748, 0.99946, 0.99987, 0.99996, 0.99999, 1.00000, 1.00000, 0.16667, 0.41476, 0.67268,
                 0.84633, 0.93614, 0.97550, 0.99103, 0.99884, 0.99984, 0.99998, 1.00000, 1.00000, 1.00000, 1.00000,
                 0.16667, 0.41586, 0.67605, 0.85129, 0.94078, 0.97877, 0.99292, 0.99930, 0.99993, 0.99999, 1.00000,
                 1.00000, 1.00000, 1.00000, 0.16667, 0.41653, 0.67810, 0.85430, 0.94356, 0.98066, 0.99396, 0.99950,
                 0.99996, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.16667, 0.41698, 0.67947, 0.85632, 0.94540,
                 0.98189, 0.99461, 0.99962, 0.99998, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.16667, 0.41810,
                 0.68294, 0.86141, 0.94998, 0.98483, 0.99607, 0.99982, 0.99999, 1.00000, 1.00000, 1.00000, 1.00000,
                 1.00000, 0.16667, 0.41847, 0.68411, 0.86312, 0.95149, 0.98577, 0.99651, 0.99987, 1.00000, 1.00000,
                 1.00000, 1.00000, 1.00000, 1.00000, 0.16667, 0.41866, 0.68470, 0.86398, 0.95225, 0.98623, 0.99672,
                 0.99989, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.16667, 0.41877, 0.68505, 0.86449,
                 0.95270, 0.98650, 0.99684, 0.99990, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 1.00000, 0.16667,
                 0.41900, 0.68576, 0.86552, 0.95360, 0.98705, 0.99707, 0.99992, 1.00000, 1.00000, 1.00000, 1.00000,
                 1.00000, 1.00000, 0.16667, 0.41911, 0.68612, 0.86604, 0.95405, 0.98731, 0.99719, 0.99993, 1.00000,
                 1.00000, 1.00000, 1.00000, 1.00000, 1.00000]
    tolerance = 1.0e-5
    i = 0
    while i < len(ns):
        f1 = BivariateCumulativeStudentDistribution(ns[i], 0.5)
        f2 = BivariateCumulativeStudentDistribution(ns[i], -0.5)
        j = 0
        while j < len(xs):
            calculated1 = f1(xs[j], xs[j])
            reference1 = expected1[i * len(xs) + j]
            calculated2 = f2(xs[j], xs[j])
            reference2 = expected2[i * len(xs) + j]
            if abs(calculated1 - reference1) > tolerance:
                raise QTError(
                    f"Failed to reproduce CDF value at [xs[j]]\n calculated: [calculated1] \n expected: [reference1]")
            if abs(calculated2 - reference2) > tolerance:
                raise QTError(
                    f"Failed to reproduce CDF value at [xs[j]] \n calculated: [calculated2] \n expected: [reference1]")
            j += 1
        i += 1

    # a few more random cases
    cases = [
        [2, -1.0, 5.0, 8.0, 0.973491],
        [2, 1.0, -2.0, 8.0, 0.091752],
        [2, 1.0, 5.25, -9.5, 0.005450],
        [3, -0.5, -5.0, -5.0, 0.000220],
        [4, -1.0, -8.0, 7.5, 0.0],
        [4, 0.5, -5.5, 10.0, 0.002655],
        [4, 1.0, -5.0, 6.0, 0.003745],
        [4, 1.0, 6.0, 5.5, 0.997336],
        [5, -0.5, -7.0, -6.25, 0.000004],
        [5, -0.5, 3.75, -7.25, 0.000166],
        [5, -0.5, 7.75, -1.25, 0.133073],
        [6, 0.0, 7.5, 3.25, 0.991149],
        [7, -0.5, -1.0, -8.5, 0.000001],
        [7, -1.0, -4.25, -4.0, 0.0],
        [7, 0.0, 0.5, -2.25, 0.018819],
        [8, -1.0, 8.25, 1.75, 0.940866],
        [8, 0.0, 2.25, 4.75, 0.972105],
        [9, -0.5, -4.0, 8.25, 0.001550],
        [9, -1.0, -1.25, -8.75, 0.0],
        [9, -1.0, 5.75, -6.0, 0.0],
        [9, 0.5, -6.5, -9.5, 0.000001],
        [9, 1.0, -2.0, 9.25, 0.038276],
        [10, -1.0, -0.5, 6.0, 0.313881],
        [10, 0.5, 0.0, 9.25, 0.5],
        [10, 0.5, 6.75, -2.25, 0.024090],
        [10, 1.0, -1.75, -1.0, 0.055341],
        [15, 0.0, -1.25, -4.75, 0.000029],
        [15, 0.0, -2.0, -1.5, 0.003411],
        [15, 0.5, 3.0, -3.25, 0.002691],
        [20, -0.5, 2.0, -1.25, 0.098333],
        [20, -1.0, 3.0, 8.0, 0.996462],
        [20, 0.0, -7.5, 1.5, 0.0],
        [20, 0.5, 1.25, 9.75, 0.887136],
        [25, -1.0, -4.25, 5.0, 0.000111],
        [25, 0.5, 9.5, -1.5, 0.073069],
        [25, 1.0, -6.5, -3.25, 0.0],
        [30, -1.0, -7.75, 10.0, 0.0],
        [30, 1.0, 0.5, 9.5, 0.689638],
        [60, -1.0, -3.5, -8.25, 0.0],
        [60, -1.0, 4.25, 0.75, 0.771869],
        [60, -1.0, 5.75, 3.75, 0.9998],
        [60, 0.5, -4.5, 8.25, 0.000016],
        [60, 1.0, 6.5, -4.0, 0.000088],
        [90, -0.5, -3.75, -2.75, 0.0],
        [90, 0.5, 8.75, -7.0, 0.0],
        [120, 0.0, -3.5, -9.25, 0.0],
        [120, 0.0, -8.25, 5.0, 0.0],
        [120, 1.0, -0.75, 3.75, 0.227361],
        [120, 1.0, -3.5, -8.0, 0.0],
        [150, 0.0, 10.0, -1.75, 0.041082],
        [300, -0.5, -6.0, 3.75, 0.0],
        [300, -0.5, 3.5, -4.5, 0.000004],
        [300, 0.0, 6.5, -5.0, 0.0],
        [600, -0.5, 9.25, 1.5, 0.93293],
        [600, -1.0, -9.25, 1.5, 0.0],
        [600, 0.5, -5.0, 8.0, 0.0],
        [600, 1.0, -2.75, -9.0, 0.0],
        [1000, -0.5, -2.5, 0.25, 0.000589],
        [1000, -0.5, 3.0, 1.0, 0.839842],
        [2000, -1.0, 9.0, -4.75, 0.000001],
        [2000, 0.5, 9.75, 7.25, 1.0],
        [2000, 1.0, 0.75, -9.0, 0.0],
        [5000, -0.5, 9.75, 5.5, 1.0],
        [5000, -1.0, 6.0, 1.0, 0.841321],
        [5000, 1.0, 4.0, -7.75, 0.0],
        [10000, 0.5, 1.5, 6.0, 0.933177]
    ]
    tolerance = 1.0e-6
    for i in cases:
        f = BivariateCumulativeStudentDistribution(i[0], i[1])
        calculated = f(i[2], i[3])
        expected = i[4]
        if abs(calculated - expected) > tolerance:
            raise QTError(
                f"Failed to reproduce CDF value:\n n: {i[0]} \n rho: {i[1]} \n x: {i[2]} \n y: {i[3]} \n  calculated:"
                f" {calculated} \n expected: {expected}")


def test_bivariate_cumulative_student_vs_bivariate():
    print("Testing bivariate cumulative Student t distribution for large N...")

    n = 10000  # for this value, the distribution should be close to a bivariate normal distribution.

    rho = -1
    while rho < 1.01:
        T = BivariateCumulativeStudentDistribution(n, rho)
        N = BivariateCumulativeNormalDistributionWe04DP(rho)

        avg_diff = 0.0
        m = 0
        tolerance = 4.0e-5
        x = -10
        while x < 10.1:
            y = -10
            while y < 10.1:
                calculated = T(x, y)
                expected = N(x, y)
                diff = abs(calculated - expected)
                if diff > tolerance:
                    raise QTError(
                        f"Failed to reproduce limit value: \n rho: {rho} \n x: {x} \n y: {y}\n calculated: "
                        f"{calculated} \n expected: {expected}")

                avg_diff += diff
                m += 1
                y += 0.25
            x += 0.25
        avg_diff /= m
        if avg_diff > 3.0e-6:
            raise QTError(
                f"Failed to reproduce average limit value: \n rho: {rho} \n average error:{avg_diff}")
        rho += 0.25


def test_inv_cdf_via_stochastic_collocation():
    print("Testing inverse CDF based on stochastic collocation...")
    k = 3.0
    lambda_ = 1.0

    inv_normal_cdf = InverseCumulativeNormal()
    normal_cdf = CumulativeNormalDistribution()
    inv_cdf = InverseNonCentralChiSquared(k, lambda_)
    sc_inv_cdf_10 = StochasticCollocationInvCDF(inv_cdf, 10)

    # low precision
    x = -3
    while x < 3.0:
        u = normal_cdf(x)

        calculated1 = sc_inv_cdf_10(u)
        calculated2 = sc_inv_cdf_10.value(x)
        expected = inv_cdf(u)

        if abs(calculated1 - calculated2) > 1e-6:
            raise QTError(
                f"Failed to reproduce equal stochastic collocation inverse CDF\n x: {x}\n"
                f"calculated via normal distribution : {calculated2} \n calculated via uniform distribution: "
                f"{calculated1} \n  diff: {calculated1 - calculated2}")

        tol = 1e-2
        if abs(calculated2 - expected) > tol:
            raise QTError(
                f"Failed to reproduce invCDF with stochastic collocation method\n x: {x}\n invCDF:{expected} \n"
                f"scInvCDF: {calculated2} \n diff: {abs(expected - calculated2)} \n tol:{tol}")

        x += 0.1

    # high precision
    sc_inv_cdf_30 = StochasticCollocationInvCDF(inv_cdf, 30, 0.9999999)
    x = -4
    while x < 4:
        u = normal_cdf(x)

        expected = inv_cdf(u)
        calculated = sc_inv_cdf_30(u)

        tol = 1e-6
        if abs(calculated - expected) > tol:
            raise QTError(
                f"Failed to reproduce invCDF with stochastic collocation method \n x:{x}\n invCDF: {expected}\n "
                f"scInvCDF:{calculated}\n diff: {abs(expected - calculated)}\n tol:{tol}")
        x += 0.1

def test_sankaran_approximation():
    print("Testing Sankaran approximation for the " + "non-central cumulative chi-square distribution...")

    dfs = [2, 2, 2, 4, 4]
    ncps = [1, 2, 3, 1, 2, 3]

    tol = 0.01
    for df in dfs:
        for ncp in ncps:
            d = NonCentralCumulativeChiSquareDistribution(df, ncp)
            sankaran = NonCentralCumulativeChiSquareSankaranApprox(df, ncp)
            x = 0.25
            while x < 10:
                expected = d(x)
                calculated = sankaran(x)
                diff = abs(expected - calculated)

                if diff > tol:
                    raise QTError(f"Failed to match accuracy of Sankaran approximation\n df: {df}\n ncp: {ncp}\n x: {x}\n expected: {expected}\n calculated: {calculated}\n diff: {diff}\n tol:{tol}")
                x += 0.1