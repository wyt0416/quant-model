import math

from qtmodel.error import qt_require
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution, NormalDistribution, \
    InverseCumulativeNormal
from qtmodel.math.statistics.generalstatistics import GeneralStatistics
from qtmodel.types import Real


def generic_gaussian_statistics(class_name):

    class GenericGaussianStatistics(class_name):

        def __init__(self, s):
            super(GenericGaussianStatistics, self).__init__(s=s)

        def gaussian_downside_variance(self):
            return self.gaussian_regret(0.0)

        def gaussian_regret(self, target: Real):
            """ returns the variance of observations below target """
            m = self.mean()
            std = self.standard_deviation()
            variance = std * std
            g_integral = CumulativeNormalDistribution(m, std)
            g = NormalDistribution(m, std)
            first_term = variance + m * m - 2.0 * target * m + target * target
            alfa = g_integral(target)
            second_term = m - target
            beta = variance * g(target)
            result = alfa * first_term - beta * second_term
            return result / alfa

        def gaussian_downside_deviation(self):
            """
            returns the downside deviation, defined as the
            square root of the downside variance.
            """
            return math.sqrt(self.gaussian_downside_variance())

        def gaussian_percentile(self, percentile: Real):
            """
            gaussian-assumption y-th percentile.
            percentile must be in range (0%-100%) extremes excluded.
            """
            qt_require(percentile > 0.0,
                       f"percentile ({percentile}) must be > 0.0")
            qt_require(percentile < 1.0,
                       f"percentile ({percentile}) must be < 1.0")

            g_inverse = InverseCumulativeNormal(class_name.mean(self),
                                                class_name.standard_deviation(self))
            return g_inverse(percentile)

        def gaussian_top_percentile(self, percentile: Real):
            """ percentile must be in range (0%-100%) extremes excluded """
            return self.gaussian_percentile(1.0 - percentile)

        def gaussian_potential_upside(self, percentile: Real):
            """ gaussian-assumption Potential-Upside at a given percentile """
            qt_require(1.0 > percentile >= 0.9,
                       f"percentile ({percentile}) out of range [0.9, 1)")

            result = self.gaussian_percentile(percentile)
            # potential upside must be a gain, i.e., floored at 0.0
            return max(result, 0.0)

        def gaussian_value_at_risk(self, percentile: Real):
            """ gaussian-assumption Value-At-Risk at a given percentile """
            qt_require(1.0 > percentile >= 0.9,
                       f"percentile ({percentile}) out of range [0.9, 1)")

            result = self.gaussian_percentile(1.0 - percentile)
            # VAR must be a loss
            # this means that it has to be MIN(dist(1.0-percentile), 0.0)
            # VAR must also be a positive quantity, so -MIN(*)
            return -min(result, 0.0)

        def gaussian_expected_shortfall(self, percentile: Real):
            """
            gaussian-assumption Expected Shortfall at a given percentile.
            Assuming a gaussian distribution it
            returns the expected loss in case that the loss exceeded
            a VaR threshold.
            See Artzner, Delbaen, Eber and Heath,
            "Coherent measures of risk", Mathematical Finance 9 (1999)
            """
            qt_require(1.0 > percentile >= 0.9,
                       f"percentile ({percentile}) out of range [0.9, 1)")

            m = self.mean()
            std = self.standard_deviation()
            g_inverse = InverseCumulativeNormal(m, std)
            var = g_inverse(1.0 - percentile)
            g = NormalDistribution(m, std)
            result = m - std * std * g(var) / (1.0 - percentile)
            # expectedShortfall must be a loss
            # this means that it has to be MIN(result, 0.0)
            # expectedShortfall must also be a positive quantity, so -MIN(*)
            return -min(result, 0.0)

        def gaussian_shortfall(self, target: Real):
            """ gaussian-assumption Shortfall (observations below target) """
            g_integral = CumulativeNormalDistribution(self.mean(),
                                                      self.standard_deviation())
            return g_integral(target)

        def gaussian_average_shortfall(self, target: Real):
            """ gaussian-assumption Average Shortfall (averaged shortfallness) """
            m = self.mean()
            std = self.standard_deviation()
            g_integral = CumulativeNormalDistribution(m, std)
            g = NormalDistribution(m, std)
            return (target - m) + std * std * g(target) / g_integral(target)

    return GenericGaussianStatistics


class GenericGaussianStatistics:
    """
    Statistics tool for gaussian-assumption risk measures
    This class wraps a somewhat generic statistic tool and adds
    a number of gaussian risk measures (e.g.: value-at-risk, expected
    shortfall, etc.) based on the mean and variance provided by
    the underlying statistic tool.
    """

    def __new__(cls, class_name, s):
        return generic_gaussian_statistics(class_name)(s)


GaussianStatistics = generic_gaussian_statistics(GeneralStatistics)


class StatsHolder:
    """ Helper class for precomputed distributions """

    def __init__(self, mean: Real=None, standard_deviation: Real=None, s=None):
        if s is None:
            self._mean = mean
            self._standard_deviation = standard_deviation
        else:
            self._mean = s.mean()
            self._standard_deviation = s.standard_deviation()

    def mean(self):
        return self._mean

    def standard_deviation(self):
        return self._standard_deviation
