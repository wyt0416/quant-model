from qtmodel.compounding import Compounding
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.types import Real


def black_scholes_theta(p: GeneralizedBlackScholesProcess,
                        value: Real,
                        delta: Real,
                        gamma: Real):
    """ default theta calculation for Black-Scholes options """
    u = p.state_variable().value()
    r = p.risk_free_rate().zero_rate(t=0.0, comp=Compounding.Continuous).rate()
    q = p.dividend_yield().zero_rate(t=0.0, comp=Compounding.Continuous).rate()
    v = p.local_volatility().local_vol(t=0.0, underlying_level=u)

    return r * value - (r - q) * u * delta - 0.5 * v * v * u * u * gamma


def default_theta_per_day(theta: Real):
    """ default theta-per-day calculation """
    return theta / 365.0
