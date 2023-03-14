import copy

from qtmodel.compounding import Compounding
from qtmodel.error import qt_require, qt_ensure
from qtmodel.handle import Handle
from qtmodel.instruments.oneassetoption import OneAssetOptionEngine
from qtmodel.instruments.payoffs import PlainVanillaPayoff
from qtmodel.methods.lattices.bsmlattice import BlackScholesLattice
from qtmodel.pricingengines.greeks import black_scholes_theta
from qtmodel.pricingengines.vanilla.discretizedvanillaoption import DiscretizedVanillaOption
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.termstructures.volatility.equityfx.blackconstantvol import BlackConstantVol
from qtmodel.termstructures.yield_curve.flatforward import FlatForward
from qtmodel.time.frequency import Frequency
from qtmodel.timegrid import TimeGrid


class BinomialVanillaEngine(OneAssetOptionEngine):
    """
    Pricing engine for vanilla options using binomial trees
    todo Greeks are not overly accurate. They could be improved
         by building a tree so that it has three points at the
         current time. The value would be fetched from the middle
         one, while the two side points would be used for
         estimating partial derivatives.
    """

    def __init__(self,
                 process: GeneralizedBlackScholesProcess,
                 time_steps: int,
                 class_type):
        super(BinomialVanillaEngine, self).__init__()
        self._process = process
        self._time_steps = time_steps
        self._class_type = class_type
        qt_require(time_steps >= 2,
                   f"at least 2 time steps required, {time_steps} provided")
        self.register_with(self._process)

    def calculate(self):
        rfdc = self._process.risk_free_rate().day_counter()
        divdc = self._process.dividend_yield().day_counter()
        voldc = self._process.black_volatility().day_counter()
        volcal = self._process.black_volatility().calendar()

        s0 = self._process.state_variable().value()
        qt_require(s0 > 0.0, "negative or null underlying given")
        v = self._process.black_volatility().black_vol(
            self._arguments.exercise.last_date(), s0)
        maturity_date = self._arguments.exercise.last_date()
        r = self._process.risk_free_rate().zero_rate(d=maturity_date,
                                                     day_counter=rfdc,
                                                     comp=Compounding.Continuous,
                                                     freq=Frequency.NoFrequency).rate()
        q = self._process.dividend_yield().zero_rate(d=maturity_date,
                                                     day_counter=divdc,
                                                     comp=Compounding.Continuous,
                                                     freq=Frequency.NoFrequency).rate()
        reference_date = self._process.risk_free_rate().reference_date()

        # binomial trees with constant coefficient
        flat_risk_free = Handle(FlatForward(reference_date=reference_date,
                                            forward=r,
                                            day_counter=rfdc))
        flat_dividends = Handle(FlatForward(reference_date=reference_date,
                                            forward=q,
                                            day_counter=divdc))
        flat_vol = Handle(BlackConstantVol(reference_date=reference_date,
                                           cal=volcal,
                                           volatility=v,
                                           dc=voldc))

        payoff = self._arguments.payoff
        qt_require(payoff, "non-plain payoff given")

        maturity = rfdc.year_fraction(date1=reference_date,
                                      date2=maturity_date)

        bs = GeneralizedBlackScholesProcess(x0=self._process.state_variable(),
                                            dividend_ts=flat_dividends,
                                            risk_free_ts=flat_risk_free,
                                            black_vol_ts=flat_vol)

        grid = TimeGrid(end=maturity,
                        steps=self._time_steps)

        tree = self._class_type(bs,
                                maturity,
                                self._time_steps,
                                payoff.strike())

        lattice = BlackScholesLattice(tree, r, maturity, self._time_steps)

        option = DiscretizedVanillaOption(self._arguments, self._process, grid)

        option.initialize(lattice, maturity)

        # Partial derivatives calculated from various points in the
        # binomial tree
        # (see J.C.Hull, "Options, Futures and other derivatives", 6th edition, pp 397/398)

        # Rollback to third-last step, and get underlying prices (s2) &
        # option values (p2) at this point
        option.rollback(grid[2])
        va2 = copy.deepcopy(option.values())
        qt_ensure(len(va2) == 3, "Expect 3 nodes in grid at second step")
        p2u = va2[2]  # up
        p2m = va2[1]  # mid
        p2d = va2[0]  # down (low)
        s2u = lattice.underlying(2, 2)  # up price
        s2m = lattice.underlying(2, 1)  # middle price
        s2d = lattice.underlying(2, 0)  # down (low) price

        # calculate gamma by taking the first derivate of the two deltas
        delta2u = (p2u - p2m) / (s2u - s2m)
        delta2d = (p2m - p2d) / (s2m - s2d)
        gamma = (delta2u - delta2d) / ((s2u - s2d) / 2)

        # Rollback to second-last step, and get option values (p1) at
        # this point
        option.rollback(grid[1])
        va = copy.deepcopy(option.values())
        qt_ensure(len(va) == 2, "Expect 2 nodes in grid at first step")
        p1u = va[1]
        p1d = va[0]
        s1u = lattice.underlying(1, 1)  # up (high) price
        s1d = lattice.underlying(1, 0)  # down (low) price

        delta = (p1u - p1d) / (s1u - s1d)

        # Finally, rollback to t=0
        option.rollback(0.0)
        p0 = option.present_value()

        # Store results
        self._results.value = p0
        self._results.delta = delta
        self._results.gamma = gamma
        self._results.theta = black_scholes_theta(self._process,
                                                  self._results.value,
                                                  self._results.delta,
                                                  self._results.gamma)
