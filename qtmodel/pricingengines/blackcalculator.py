import math
import sys

from qtmodel.error import QTError, qt_require
from qtmodel.instruments.payoffs import PlainVanillaPayoff, CashOrNothingPayoff, AssetOrNothingPayoff, GapPayoff, \
    StrikedTypePayoff
from qtmodel.math.comparison import close
from qtmodel.math.distributions.normaldistribution import CumulativeNormalDistribution
from qtmodel.mathconstants import M_SQRT_2, M_1_SQRTPI
from qtmodel.option import OptionTypes
from qtmodel.patterns.visitor import Visitor
from qtmodel.payoff import Payoff
from qtmodel.types import Real


class BlackCalculator:
    """ Black 1976 calculator class """

    def __init__(self,
                 payoff: StrikedTypePayoff = None,
                 option_type: OptionTypes = None,
                 strike: Real = None,
                 forward: Real = None,
                 std_dev: Real = None,
                 discount: Real = 1.0):
        self._d1 = self._d2 = self._alpha = self._beta = self._DalphaDd1 = self._DbetaDd2 = None
        self._n_d1 = self._cum_d1 = self._n_d2 = self._cum_d2 = None
        self._x = self._DxDs = self._DxDstrike = None
        if payoff is not None and forward is not None and std_dev is not None:
            self._strike = payoff.strike()
            self._forward = forward
            self._std_dev = std_dev
            self._discount = discount
            self._variance = std_dev * std_dev
            self.initialize(payoff)
        elif option_type is not None and strike is not None and \
                forward is not None and std_dev is not None:
            self._strike = strike
            self._forward = forward
            self._std_dev = std_dev
            self._discount = discount
            self._variance = std_dev * std_dev
            self.initialize(PlainVanillaPayoff(option_type, strike))
        else:
            raise QTError("it's not in the two scenarios")

    def initialize(self, p: StrikedTypePayoff):
        qt_require(self._strike >= 0.0,
                   f"strike ({self._strike}) must be non-negative")
        qt_require(self._forward > 0.0,
                   f"forward ({self._forward}) must be positive")
        qt_require(self._std_dev >= 0.0,
                   f"std_dev ({self._std_dev}) must be non-negative")
        qt_require(self._discount > 0.0,
                   f"discount ({self._discount}) must be positive")

        if self._std_dev >= sys.float_info.epsilon:
            if close(self._strike, 0.0):
                self._d1 = sys.float_info.max
                self._d2 = sys.float_info.max
                self._cum_d1 = 1.0
                self._cum_d2 = 1.0
                self._n_d1 = 0.0
                self._n_d2 = 0.0
            else:
                self._d1 = math.log(self._forward / self._strike) / self._std_dev + 0.5 * self._std_dev
                self._d2 = self._d1 - self._std_dev
                f = CumulativeNormalDistribution()
                self._cum_d1 = f(self._d1)
                self._cum_d2 = f(self._d2)
                self._n_d1 = f.derivative(self._d1)
                self._n_d2 = f.derivative(self._d2)
        else:
            if close(self._forward, self._strike):
                self._d1 = 0
                self._d2 = 0
                self._cum_d1 = 0.5
                self._cum_d2 = 0.5
                self._n_d1 = M_SQRT_2 * M_1_SQRTPI
                self._n_d2 = M_SQRT_2 * M_1_SQRTPI
            elif self._forward > self._strike:
                self._d1 = sys.float_info.max
                self._d2 = sys.float_info.max
                self._cum_d1 = 1.0
                self._cum_d2 = 1.0
                self._n_d1 = 0.0
                self._n_d2 = 0.0
            else:
                self._d1 = -sys.float_info.max
                self._d2 = -sys.float_info.max
                self._cum_d1 = 0.0
                self._cum_d2 = 0.0
                self._n_d1 = 0.0
                self._n_d2 = 0.0

        self._x = self._strike
        self._DxDstrike = 1.0

        # the following one will probably disappear as soon as
        # super-share will be properly handled
        self._DxDs = 0.0

        # this part is always executed.
        # in case of plain-vanilla payoffs, it is also the only part
        # which is executed.
        if p.option_type() == OptionTypes.Call:
            self._alpha = self._cum_d1  # N(d1)
            self._DalphaDd1 = self._n_d1  # n(d1)
            self._beta = -self._cum_d2  # -N(d2)
            self._DbetaDd2 = -  self._n_d2  # -n(d2)
        elif p.option_type() == OptionTypes.Put:
            self._alpha = -1.0 + self._cum_d1  # -N(-d1)
            self._DalphaDd1 = self._n_d1  # n( d1)
            self._beta = 1.0 - self._cum_d2  # N(-d2)
            self._DbetaDd2 = -  self._n_d2  # -n( d2)
        else:
            QTError("invalid option type")

        # now dispatch on type.

        calc = BlackCalculatorCalculator(self)
        p.accept(calc)

    def value(self):
        result = self._discount * (self._forward * self._alpha + self._x * self._beta)
        return result

    def delta_forward(self):
        """ Sensitivity to change in the underlying forward price. """
        temp = self._std_dev * self._forward
        dalpha_dforward = self._DalphaDd1 / temp
        dbeta_dforward = self._DbetaDd2 / temp
        temp2 = dalpha_dforward * self._forward + self._alpha + dbeta_dforward * self._x  # DXDforward = 0.0

        return self._discount * temp2

    def delta(self, spot: Real):
        """ Sensitivity to change in the underlying spot price. """
        qt_require(spot > 0.0, f"positive spot value required: {spot} not allowed")

        DforwardDs = self._forward / spot

        temp = self._std_dev * spot
        DalphaDs = self._DalphaDd1 / temp
        DbetaDs = self._DbetaDd2 / temp
        temp2 = DalphaDs * self._forward + self._alpha * DforwardDs + DbetaDs * self._x + self._beta * self._DxDs

        return self._discount * temp2

    def elasticity_forward(self):
        """ Sensitivity in percent to a percent change in the underlying forward price. """
        val = self.value()
        del_ = self.delta_forward()
        if val > sys.float_info.epsilon:
            return del_ / val * self._forward
        elif abs(del_) < sys.float_info.epsilon:
            return 0.0
        elif del_ > 0.0:
            return sys.float_info.max
        else:
            return -sys.float_info.max

    def elasticity(self, spot: Real):
        """ Sensitivity in percent to a percent change in the underlying spot price. """
        val = self.value()
        del_ = self.delta(spot)
        if val > sys.float_info.epsilon:
            return del_ / val * spot
        elif abs(del_) < sys.float_info.epsilon:
            return 0.0
        elif del_ > 0.0:
            return sys.float_info.max
        else:
            return -sys.float_info.max

    def gamma_forward(self):
        """ Second order derivative with respect to change in the underlying forward price. """
        temp = self._std_dev * self._forward
        DalphaDforward = self._DalphaDd1 / temp
        DbetaDforward = self._DbetaDd2 / temp

        D2alphaDforward2 = - DalphaDforward / self._forward * (1 + self._d1 / self._std_dev)
        D2betaDforward2 = - DbetaDforward / self._forward * (1 + self._d2 / self._std_dev)

        temp2 = D2alphaDforward2 * self._forward + 2.0 * DalphaDforward + D2betaDforward2 * self._x  # DXDforward = 0.0

        return self._discount * temp2

    def gamma(self, spot: Real):
        """ Second order derivative with respect to change in the underlying spot price. """
        qt_require(spot > 0.0, f"positive spot value required: {spot} not allowed")

        DforwardDs = self._forward / spot

        temp = self._std_dev * spot
        DalphaDs = self._DalphaDd1 / temp
        DbetaDs = self._DbetaDd2 / temp

        D2alphaDs2 = - DalphaDs / spot * (1 + self._d1 / self._std_dev)
        D2betaDs2 = - DbetaDs / spot * (1 + self._d2 / self._std_dev)

        temp2 = D2alphaDs2 * self._forward + 2.0 * DalphaDs * DforwardDs + D2betaDs2 * self._x + 2.0 * DbetaDs * self._DxDs

        return self._discount * temp2

    def theta(self, spot: Real, maturity: Real):
        """ Sensitivity to time to maturity. """
        qt_require(maturity >= 0.0, f"maturity ({maturity}) must be non-negative")
        if close(maturity, 0.0):
            return 0.0
        return -(math.log(self._discount) * self.value() + math.log(self._forward / spot) * spot * self.delta(
            spot) + 0.5 * self._variance * spot * spot * self.gamma(spot)) / maturity

    def theta_per_day(self, spot: Real, maturity: Real):
        """ Sensitivity to time to maturity per day, assuming 365 day per year. """
        return self.theta(spot, maturity) / 365.0

    def vega(self, maturity: Real):
        """ Sensitivity to volatility. """
        qt_require(maturity >= 0.0, "negative maturity not allowed")

        temp = math.log(self._strike / self._forward) / self._variance
        # actually DalphaDsigma / SQRT(T)
        DalphaDsigma = self._DalphaDd1 * (temp + 0.5)
        DbetaDsigma = self._DbetaDd2 * (temp - 0.5)

        temp2 = DalphaDsigma * self._forward + DbetaDsigma * self._x

        return self._discount * math.sqrt(maturity) * temp2

    def rho(self, maturity: Real):
        """ Sensitivity to discounting rate. """
        qt_require(maturity >= 0.0, "negative maturity not allowed")

        # actually DalphaDr / T
        DalphaDr = self._DalphaDd1 / self._std_dev
        DbetaDr = self._DbetaDd2 / self._std_dev
        temp = DalphaDr * self._forward + self._alpha * self._forward + DbetaDr * self._x

        return maturity * (self._discount * temp - self.value())

    def dividend_rho(self, maturity: Real):
        """ Sensitivity to dividend/growth rate. """
        qt_require(maturity >= 0.0, "negative maturity not allowed")

        # actually DalphaDq / T
        DalphaDq = -self._DalphaDd1 / self._std_dev
        DbetaDq = -self._DbetaDd2 / self._std_dev

        temp = DalphaDq * self._forward - self._alpha * self._forward + DbetaDq * self._x

        return maturity * self._discount * temp

    def itm_cash_probability(self):
        """
        Probability of being in the money in the bond martingale measure, i.e. N(d2).
        It is a risk-neutral probability, not the real world one.
        """
        return self._cum_d2

    def itm_asset_probability(self):
        """
        Probability of being in the money in the asset martingale measure, i.e. N(d1).
        It is a risk-neutral probability, not the real world one.
        """
        return self._cum_d1

    def strike_sensitivity(self):
        """ Sensitivity to strike. """
        temp = self._std_dev * self._strike
        DalphaDstrike = -self._DalphaDd1 / temp
        DbetaDstrike = -self._DbetaDd2 / temp

        temp2 = DalphaDstrike * self._forward + DbetaDstrike * self._x + self._beta * self._DxDstrike

        return self._discount * temp2

    def alpha(self):
        return self._alpha

    def beta(self):
        return self._beta


class BlackCalculatorCalculator(Visitor):

    def __init__(self, black: BlackCalculator):
        self._black = black

    def visit(self, payoff: Payoff):
        if isinstance(payoff, PlainVanillaPayoff):
            pass
        elif isinstance(payoff, CashOrNothingPayoff):
            self._black._alpha = self._black._DalphaDd1 = 0.0
            self._black._x = payoff.cash_payoff()
            self._black._DxDstrike = 0.0
            if payoff.option_type() == OptionTypes.Call:
                self._black._beta = self._black._cum_d2
                self._black._DbetaDd2 = self._black._n_d2
            elif payoff.option_type() == OptionTypes.Put:
                self._black._beta = 1.0 - self._black._cum_d2
                self._black._DbetaDd2 = -self._black._n_d2
            else:
                raise QTError("invalid option type")
        elif isinstance(payoff, AssetOrNothingPayoff):
            self._black._beta = self._black._DbetaDd2 = 0.0
            if payoff.option_type() == OptionTypes.Call:
                self._black._alpha = self._black._cum_d1
                self._black._DalphaDd1 = self._black._n_d1
            elif payoff.option_type() == OptionTypes.Put:
                self._black._alpha = 1.0 - self._black._cum_d1
                self._black._DalphaDd1 = -self._black._n_d1
            else:
                raise QTError("invalid option type")
        elif isinstance(payoff, GapPayoff):
            self._black._x = payoff.second_strike()
            self._black._DxDstrike = 0.0
        else:
            raise QTError("invalid payoff type")
