import math
from datetime import datetime

from qtmodel.compounding import Compounding
from qtmodel.error import QTError
from qtmodel.handle import Handle, RelinkableHandle
from qtmodel.processes.eulerdiscretization import EulerDiscretization
from qtmodel.stochasticprocess import StochasticProcess1D, StochasticProcess1DDiscretization
from qtmodel.termstructures.volatility.equityfx.localconstantvol import LocalConstantVol
from qtmodel.termstructures.volatility.equityfx.localvolsurface import LocalVolSurface
from qtmodel.termstructures.yield_curve.flatforward import FlatForward
from qtmodel.time.calendars.nullcalendar import NullCalendar
from qtmodel.time.daycounters.actual365fixed import Actual365Fixed
from qtmodel.time.frequency import Frequency
from qtmodel.types import Real


class GeneralizedBlackScholesProcess(StochasticProcess1D):
    """ Generalized Black-Scholes stochastic process """

    def __init__(self,
                 x0: Handle,
                 dividend_ts: Handle,
                 risk_free_ts: Handle,
                 black_vol_ts: Handle,
                 disc: StochasticProcess1DDiscretization = EulerDiscretization(),
                 force_discretization: bool = False,
                 local_vol_ts: Handle = None):
        if local_vol_ts is None:
            super(GeneralizedBlackScholesProcess, self).__init__(disc=disc)
            self._x0 = x0
            self._risk_free_rate = risk_free_ts
            self._dividend_yield = dividend_ts
            self._black_volatility = black_vol_ts
            self._force_discretization = force_discretization
            self._has_external_local_vol = False
            self._updated = False
            self._is_strike_independent = False
            self.register_with(self._x0)
            self.register_with(self._risk_free_rate)
            self.register_with(self._dividend_yield)
            self.register_with(self._black_volatility)
        else:
            super(GeneralizedBlackScholesProcess, self).__init__(disc=EulerDiscretization())
            self._x0 = x0
            self._risk_free_rate = risk_free_ts
            self._dividend_yield = dividend_ts
            self._black_volatility = black_vol_ts
            self._external_local_vol_ts = local_vol_ts
            self._force_discretization = False
            self._has_external_local_vol = False
            self._updated = False
            self._is_strike_independent = False
            self.register_with(self._x0)
            self.register_with(self._risk_free_rate)
            self.register_with(self._dividend_yield)
            self.register_with(self._black_volatility)
            self.register_with(self._external_local_vol_ts)

        self._local_volatility: RelinkableHandle = RelinkableHandle()

    def x0(self):
        return self._x0.value()

    def drift(self, t: Real, x: Real):
        sigma = self.diffusion(t, x)
        # we could be more anticipatory if we know the right dt
        # for which the drift will be used
        t1 = t + 0.0001
        return self._risk_free_rate.forward_rate(t1=t,
                                                 t2=t1,
                                                 comp=Compounding.Continuous,
                                                 freq=Frequency.NoFrequency,
                                                 extrapolate=True).rate() - \
               self._dividend_yield.forward_rate(t1=t,
                                                 t2=t1,
                                                 comp=Compounding.Continuous,
                                                 freq=Frequency.NoFrequency,
                                                 extrapolate=True).rate() - 0.5 * sigma * sigma

    def diffusion(self, t: Real, x: Real):
        return self.local_volatility().local_vol(t=t, underlying_level=x, extrapolate=True)

    def local_volatility(self):
        if self._has_external_local_vol:
            return self._external_local_vol_ts

        if not self._updated:
            self._is_strike_independent = True

            # constant Black vol?
            const_vol = self.black_volatility()
            if const_vol is not None:
                # ok, the local vol is constant too.
                self._local_volatility.link_to(LocalConstantVol(reference_date=const_vol.reference_date(),
                                                                volatility=const_vol.black_vol(0.0, self._x0.value()),
                                                                day_counter=const_vol.day_counter()))
                self._updated = True
                return self._local_volatility

            # ok, so it's not constant. Maybe it's strike-independent?
            vol_curve = self.black_volatility()
            if vol_curve is not None:
                # ok, we can use the optimized algorithm
                self._local_volatility.link_to(Handle(vol_curve))
                self._updated = True
                return self._local_volatility

            # ok, so it's strike-dependent. Never mind.
            self._local_volatility.link_to(LocalVolSurface(black_ts=self._black_volatility,
                                                           risk_free_ts=self._risk_free_rate,
                                                           dividend_ts=self._dividend_yield,
                                                           underlying=self._x0.value()))
            self._updated = True
            self._is_strike_independent = False
            return self._local_volatility

        else:
            return self._local_volatility

    def black_volatility(self):
        return self._black_volatility

    def apply(self, x0: Real, dx: Real):
        return x0 * math.exp(dx)

    def expectation(self, t0: Real, x0: Real, dt: Real):
        self.local_volatility()  # trigger update
        if self._is_strike_independent and not self._force_discretization:
            # exact value for curves
            return x0 * math.exp(dt * (self._risk_free_rate.forwardRate(
                t1=t0,
                t2=t0 + dt,
                comp=Compounding.Continuous,
                freq=Frequency.NoFrequency,
                extrapolate=True
            ) - self._dividend_yield.forwardRate(
                t1=t0,
                t2=t0 + dt,
                comp=Compounding.Continuous,
                freq=Frequency.NoFrequency,
                extrapolate=True)))
        else:
            QTError("not implemented")

    def std_deviation(self, t0: Real, x0: Real, dt: Real):
        self.local_volatility()  # trigger update
        if self._is_strike_independent and not self._force_discretization:
            # exact value for curves
            return math.sqrt(self.variance(t0, x0, dt))

        else:
            return self._discretization.diffusion(self, t0, x0, dt)

    def variance(self, t0: Real, x0: Real, dt: Real):
        self.local_volatility()  # trigger update
        if self._is_strike_independent and not self._force_discretization:
            # exact value for curves
            return self._black_volatility.black_variance(t0 + dt, 0.01) - self._black_volatility.black_variance(t0,
                                                                                                                0.01)
        else:
            return self._discretization.variance(self, t0, x0, dt)

    def evolve(self, t0: Real, x0: Real, dt: Real, dw: Real):
        self.local_volatility()  # trigger update
        if self._is_strike_independent and not self._force_discretization:
            # exact value for curves
            var = self.variance(t0, x0, dt)
            drift = (self._risk_free_rate.forward_rate(t1=t0,
                                                       t2=t0 + dt,
                                                       comp=Compounding.Continuous,
                                                       freq=Frequency.NoFrequency,
                                                       extrapolate=True) -
                     self._dividend_yield.forward_rate(t1=t0,
                                                       t2=t0 + dt,
                                                       comp=Compounding.Continuous,
                                                       freq=Frequency.NoFrequency,
                                                       extrapolate=True)) * dt - 0.5 * var
            return self.apply(x0, math.sqrt(var) * dw + drift)
        else:
            return self.apply(x0, self._discretization.drift(self, t0, x0, dt) + self.std_deviation(t0, x0, dt) * dw)

    def time(self, d: datetime):
        return self._risk_free_rate.day_counter().year_fraction(self._risk_free_rate.reference_date(), d)

    def update(self):
        self._updated = False
        StochasticProcess1D.update(self)

    def state_variable(self):
        return self._x0

    def dividend_yield(self):
        return self._dividend_yield

    def risk_free_rate(self):
        return self._risk_free_rate


class BlackScholesProcess(GeneralizedBlackScholesProcess):
    """ Black-Scholes (1973) stochastic process """

    def __init__(self,
                 x0: Handle,
                 risk_free_ts: Handle,
                 black_vol_ts: Handle,
                 d: StochasticProcess1DDiscretization = EulerDiscretization(),
                 force_discretization: bool = False):
        super(BlackScholesProcess, self).__init__(x0=x0,
                                                  dividend_ts=FlatForward(settlement_days=0,
                                                                          calendar=NullCalendar(),
                                                                          forward=0.0,
                                                                          day_counter=Actual365Fixed()),
                                                  risk_free_ts=risk_free_ts,
                                                  black_vol_ts=black_vol_ts,
                                                  disc=d,
                                                  force_discretization=force_discretization)


class BlackScholesMertonProcess(GeneralizedBlackScholesProcess):
    """ Merton (1973) extension to the Black-Scholes stochastic process """

    def __init__(self,
                 x0: Handle,
                 dividend_ts: Handle,
                 risk_free_ts: Handle,
                 black_vol_ts: Handle,
                 d: StochasticProcess1DDiscretization = EulerDiscretization(),
                 force_discretization: bool = False):
        super(BlackScholesMertonProcess, self).__init__(x0=x0,
                                                        dividend_ts=dividend_ts,
                                                        risk_free_ts=risk_free_ts,
                                                        black_vol_ts=black_vol_ts,
                                                        disc=d,
                                                        force_discretization=force_discretization)


class BlackProcess(GeneralizedBlackScholesProcess):
    """ Black (1976) stochastic process """

    def __init__(self,
                 x0: Handle,
                 risk_free_ts: Handle,
                 black_vol_ts: Handle,
                 d: StochasticProcess1DDiscretization = EulerDiscretization(),
                 force_discretization: bool = False):
        super(BlackProcess, self).__init__(x0=x0,
                                           dividend_ts=risk_free_ts,
                                           risk_free_ts=risk_free_ts,
                                           black_vol_ts=black_vol_ts,
                                           disc=d,
                                           force_discretization=force_discretization)


class GarmanKohlagenProcess(GeneralizedBlackScholesProcess):
    """ Garman-Kohlhagen (1983) stochastic process """

    def __init__(self,
                 x0: Handle,
                 foreign_risk_free_ts: Handle,
                 domestic_risk_free_ts: Handle,
                 black_vol_ts: Handle,
                 d: StochasticProcess1DDiscretization = EulerDiscretization(),
                 force_discretization: bool = False):
        super(GarmanKohlagenProcess, self).__init__(x0=x0,
                                                    dividend_ts=foreign_risk_free_ts,
                                                    risk_free_ts=domestic_risk_free_ts,
                                                    black_vol_ts=black_vol_ts,
                                                    disc=d,
                                                    force_discretization=force_discretization)
