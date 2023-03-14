import math

from qtmodel.error import qt_require, qt_ensure
from qtmodel.math.statistics.gaussianstatistics import GaussianStatistics
from qtmodel.types import Real


def generic_risk_statistics(class_name):

    class GenericRiskStatistics(class_name):

        def semi_variance(self):
            """ returns the variance of observations below the mean """
            return self.regret(self.mean())

        def semi_deviation(self):
            """
            returns the semi deviation, defined as the
            square root of the semi variance.
            """
            return math.sqrt(self.semi_variance())

        def downside_variance(self):
            """ returns the variance of observations below 0.0 """
            return self.regret(0.0)

        def downside_deviation(self):
            """
            returns the downside deviation, defined as the
            square root of the downside variance.
            """
            return math.sqrt(self.downside_variance())

        def regret(self, target: Real):
            """
            returns the variance of observations below target.
            See Dembo and Freeman, "The Rules Of Risk", Wiley (2001).
            """
            # average over the range below the target
            result = self.expectation_value(lambda xi: math.pow((xi - target), 2),
                                            lambda xi: xi < target)
            x = result[0]
            N = result[1]
            qt_require(N > 1,
                       "samples under target <= 1, unsufficient")
            return (N / (N - 1.0)) * x

        def potential_upside(self, centile: Real):
            """ potential upside (the reciprocal of VAR) at a given percentile """
            qt_require(0.9 <= centile < 1.0,
                       f"percentile ({centile}) out of range [0.9, 1.0)")

            # potential upside must be a gain, i.e., floored at 0.0
            return max(self.percentile(centile), 0.0)

        def value_at_risk(self, centile: Real):
            """ value-at-risk at a given percentile """
            qt_require(0.9 <= centile < 1.0,
                       f"percentile ({centile}) out of range [0.9, 1.0)")

            # must be a loss, i.e., capped at 0.0 and negated
            return -min(self.percentile(1.0-centile), 0.0)

        def expected_shortfall(self, centile: Real):
            """
            expected shortfall at a given percentile
            returns the expected loss in case that the loss exceeded
            a VaR threshold.

            See Artzner, Delbaen, Eber and Heath,
            "Coherent measures of risk", Mathematical Finance 9 (1999) """
            qt_require(0.9 <= centile < 1.0,
                       f"percentile ({centile}) out of range [0.9, 1.0)")

            qt_ensure(self.samples() != 0, "empty sample set")
            target = -self.value_at_risk(centile)
            result = self.expectation_value(lambda xi: xi,
                                            lambda xi: xi < target)
            x = result[0]
            N = result[1]
            qt_ensure(N != 0, "no data below the target")
            # must be a loss, i.e., capped at 0.0 and negated
            return -min(x, 0.0)

        def shortfall(self, target: Real):
            """ probability of missing the given target """
            qt_ensure(self.samples() != 0, "empty sample set")
            return self.expectation_value(lambda x: 1.0 if x < target else 0.0)[0]

        def average_shortfall(self, target: Real):
            """ averaged shortfallness """
            result = self.expectation_value(lambda xi: target - xi,
                                            lambda xi: xi < target)
            x = result[0]
            N = result[1]
            qt_ensure(N != 0, "no data below the target")
            return x

    return GenericRiskStatistics


class GenericRiskStatistics:
    """
    empirical-distribution risk measures
    This class wraps a somewhat generic statistic tool and adds
    a number of risk measures (e.g.: value-at-risk, expected
    shortfall, etc.) based on the data distribution as reported by
    the underlying statistic tool.

    todo add historical annualized volatility
    """

    def __new__(cls, class_name):
        return generic_risk_statistics(class_name)()


RiskStatistics = generic_risk_statistics(GaussianStatistics)
