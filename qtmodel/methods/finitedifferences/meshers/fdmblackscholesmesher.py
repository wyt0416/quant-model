import math

from qtmodel.error import qt_require
from qtmodel.handle import Handle
from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.math.distributions.normaldistribution import InverseCumulativeNormal
from qtmodel.methods.finitedifferences.meshers.concentrating1dmesher import Concentrating1dMesher
from qtmodel.methods.finitedifferences.meshers.fdm1dmesher import Fdm1dMesher
from qtmodel.methods.finitedifferences.meshers.uniform1dmesher import Uniform1dMesher
from qtmodel.methods.finitedifferences.utilities.fdmquantohelper import FdmQuantoHelper
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.termstructures.volatility.equityfx.blackconstantvol import BlackConstantVol
from qtmodel.termstructures.yield_curve.quantotermstructure import QuantoTermStructure
from qtmodel.types import Real


class FdmBlackScholesMesher(Fdm1dMesher):

    def __init__(self,
                 size: int,
                 process: GeneralizedBlackScholesProcess,
                 maturity: Real,
                 strike: Real,
                 x_min_constraint: Real = None,
                 x_max_constraint: Real = None,
                 eps: Real = 0.0001,
                 scale_factor: Real = 1.5,
                 c_point: tuple = None,
                 dividend_schedule: DividendSchedule = None,
                 fdm_quanto_helper: FdmQuantoHelper = None,
                 spot_adjustment: Real = 0.0):
        super(FdmBlackScholesMesher, self).__init__(size)
        S = process.x0()
        qt_require(S > 0.0, "negative or null underlying given")

        intermediate_steps = []
        for i in dividend_schedule:
            t = process.time(i.date())
            if maturity >= t >= 0.0:
                intermediate_steps.append((process.time(i.date()), i.amount()))

        intermediate_time_steps = max(2, int(24.0 * maturity))
        for i in range(intermediate_time_steps):
            intermediate_steps.append(((i + 1) * (maturity / intermediate_time_steps), 0.0))

        intermediate_steps.sort()

        r_ts = process.risk_free_rate()

        q_ts = Handle(QuantoTermStructure(process.dividend_yield(),
                                          process.risk_free_rate(),
                                          Handle(fdm_quanto_helper._f_ts),
                                          process.black_volatility(),
                                          strike,
                                          Handle(fdm_quanto_helper._fx_vol_ts),
                                          fdm_quanto_helper._exch_rate_atm_level,
                                          fdm_quanto_helper._equity_fx_correlation)) if fdm_quanto_helper is not None else process.dividend_yield()

        last_div_time = 0.0
        fwd = S + spot_adjustment
        mi = fwd
        ma = fwd

        for intermediateStep in intermediate_steps:
            div_time = intermediateStep[0]
            div_amount = intermediateStep[1]

            fwd = fwd / r_ts.discount(div_time) * r_ts.discount(last_div_time) * q_ts.discount(
                div_time) / q_ts.discount(
                last_div_time)

            mi = min(mi, fwd)
            ma = max(ma, fwd)

            fwd -= div_amount

            mi = min(mi, fwd)
            ma = max(ma, fwd)

            last_div_time = div_time

        # Set the grid boundaries
        norm_inv_eps = InverseCumulativeNormal()(1 - eps)
        sigma_sqrt_t = process.black_volatility().black_vol(maturity, strike) * math.sqrt(maturity)

        x_min = math.log(mi) - sigma_sqrt_t * norm_inv_eps * scale_factor
        x_max = math.log(ma) + sigma_sqrt_t * norm_inv_eps * scale_factor

        if x_min_constraint is not None:
            x_min = x_min_constraint
        if x_max_constraint is not None:
            x_max = x_max_constraint

        if c_point[0] is not None and x_min <= math.log(c_point[0]) <= x_max:

            helper = Concentrating1dMesher(x_min,
                                           x_max,
                                           size,
                                           (math.log(c_point[0]), c_point[1]))
        else:
            helper = Uniform1dMesher(x_min, x_max, size)

        self._locations = helper.locations()
        for i in range(len(self._locations)):
            self._dplus[i] = helper.dplus(i)
            self._dminus[i] = helper.dminus(i)

    @staticmethod
    def process_helper(s0: Handle,
                       r_ts: Handle,
                       q_ts: Handle,
                       vol: Real):
        return GeneralizedBlackScholesProcess(s0, q_ts, r_ts,
                                              Handle(BlackConstantVol(reference_date=r_ts.reference_date(),
                                                                      cal=None,
                                                                      volatility=vol,
                                                                      dc=r_ts.day_counter())))
