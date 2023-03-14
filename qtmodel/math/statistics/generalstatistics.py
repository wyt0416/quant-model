import math
import sys
from typing import List, Tuple

from qtmodel.error import qt_require
from qtmodel.types import Real


class GeneralStatistics:
    """
    Statistics tool
    This class accumulates a set of data and returns their
    statistics (e.g: mean, variance, skewness, kurtosis,
    error estimation, percentile, etc.) based on the empirical
    distribution (no gaussian assumption)

    It doesn't suffer the numerical instability problem of
    IncrementalStatistics. The downside is that it stores all
    samples, thus increasing the memory requirements.
    """

    def __init__(self):
        self._samples: List[Tuple[Real, Real]] = []
        self._sorted: bool = None
        self.reset()

    def samples(self):
        """ number of samples collected """
        return len(self._samples)

    def data(self):
        """ collected data """
        return self._samples

    def weight_sum(self):
        """ sum of data weights """
        result = 0.0
        for it in self._samples:
            result += it[1]
        return result

    def mean(self):
        """ returns the mean """
        N = self.samples()
        qt_require(N != 0, "empty sample set")
        return self.expectation_value(lambda x: x)[0]

    def variance(self):
        """ returns the variance """
        N = self.samples()
        qt_require(N > 1,
                   "sample number <=1, unsufficient")
        # Subtract the mean and square. Repeat on the whole range.
        # Hopefully, the whole thing will be inlined in a single loop.
        m = self.mean()
        s2 = self.expectation_value(lambda x: math.pow(x - m, 2))[0]
        return s2 * N / (N - 1.0)

    def standard_deviation(self):
        """
        returns the standard deviation sigma, defined as the
        square root of the variance.
        """
        return math.sqrt(self.variance())

    def error_estimate(self):
        """ returns the error estimate on the mean value """
        return math.sqrt(self.variance() / self.samples())

    def skewness(self):
        """
        returns the skewness.
        The above evaluates to 0 for a Gaussian distribution.
        """
        N = self.samples()
        qt_require(N > 2,
                   "sample number <=2, unsufficient")

        m = self.mean()
        X = self.expectation_value(lambda x: math.pow(x - m, 3))[0]
        sigma = self.standard_deviation()

        return (X / (sigma * sigma * sigma)) * (N / (N - 1.0)) * (N / (N - 2.0))

    def kurtosis(self):
        """
        returns the excess kurtosis.
        The above evaluates to 0 for a Gaussian distribution.
        """
        N = self.samples()
        qt_require(N > 3,
                   "sample number <=3, unsufficient")

        m = self.mean()
        X = self.expectation_value(lambda x: math.pow(math.pow(x - m, 2), 2))[0]
        sigma2 = self.variance()

        c1 = (N / (N - 1.0)) * (N / (N - 2.0)) * ((N + 1.0) / (N - 3.0))
        c2 = 3.0 * ((N - 1.0) / (N - 2.0)) * ((N - 1.0) / (N - 3.0))

        return c1 * (X / (sigma2 * sigma2)) - c2

    def min(self):
        """ returns the minimum sample value """
        qt_require(self.samples() > 0, "empty sample set")
        return min(self._samples)[0]

    def max(self):
        """ returns the maximum sample value """
        qt_require(self.samples() > 0, "empty sample set")
        return max(self._samples)[0]

    def expectation_value(self,
                          f,
                          in_range=lambda x: True):
        """
        The function returns a pair made of the result and
        the number of observations in the given range.
        """
        num = 0.0
        den = 0.0
        N = 0
        for i in self._samples:
            x = i[0]
            w = i[1]
            if in_range(x):
                num += f(x) * w
                den += w
                N += 1
        if N == 0:
            return sys.float_info.max, 0
        else:
            return num / den, N

    def percentile(self, percent: Real):
        qt_require(0.0 < percent <= 1.0,
                   f"percentile ({percent}) must be in (0.0, 1.0]")

        sample_weight = self.weight_sum()
        qt_require(sample_weight > 0.0,
                   "empty sample set")

        self.sort()

        k = 0  # 第一个元素的index
        l = len(self._samples) - 1  # 最后一个元素的index
        # the sum of weight is non null, therefore there's
        # at least one sample

        integral = self._samples[k][1]
        target = percent * sample_weight

        while integral < target and k != l:
            k += 1
            integral += self._samples[k][1]

        return self._samples[k][0]

    def sort(self):
        """ sort the data set in increasing order """
        if not self._sorted:
            self._samples.sort()
            self._sorted = True

    def reset(self):
        """ resets the data to a null set """
        self._samples = []
        self._sorted = True

    def add(self, value: Real, weight: Real = 1.0):
        """ adds a datum to the set, possibly with a weight """
        qt_require(weight >= 0.0, "negative weight not allowed")
        self._samples.append((value, weight))
        self._sorted = False

    def top_percentile(self, percent: Real):
        qt_require(0.0 < percent <= 1.0,
                   f"percentile ({percent}) must be in (0.0, 1.0]")

        sample_weight = self.weight_sum()
        qt_require(sample_weight > 0.0,
                   "empty sample set")

        self.sort()

        k = len(self._samples) - 1  # # 最后一个元素的index
        l = 0  # 第一个元素的index
        # the sum of weight is non null, therefore there's
        # at least one sample
        integral = self._samples[k][1]
        target = percent * sample_weight
        while integral < target and k != l:
            k -= 1
            integral += self._samples[k][1]
        return self._samples[k][0]

    def add_sequence(self, data_iterator: list, weight_iterator: list = None):
        # adds a sequence of data to the set, with default weight
        if weight_iterator is None:
            for i in data_iterator:
                self.add(i)
        # adds a sequence of data to the set, each with its weight
        else:
            for i, k in zip(data_iterator, weight_iterator):
                self.add(i, k)
