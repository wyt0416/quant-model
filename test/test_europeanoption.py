from datetime import datetime, timedelta
from enum import Enum

# utilities
import pandas as pd

from qtmodel.error import QTError, qt_ensure
from qtmodel.exercise import EuropeanExercise, Exercise
from qtmodel.handle import Handle
from qtmodel.instruments.dividendvanillaoption import DividendVanillaOption
from qtmodel.instruments.europeanoption import EuropeanOption
from qtmodel.instruments.payoffs import PlainVanillaPayoff, StrikedTypePayoff, CashOrNothingPayoff, \
    AssetOrNothingPayoff, GapPayoff
from qtmodel.instruments.vanillaoption import VanillaOption
from qtmodel.methods.finitedifferences.solvers.fdmbackwardsolver import FdmSchemeDesc
from qtmodel.methods.lattices.binomialtree import JarrowRudd, AdditiveEQPBinomialTree, Trigeorgis, Tian, LeisenReimer, \
    Joshi4, CoxRossRubinstein
from qtmodel.option import OptionTypes, Option
from qtmodel.pricingengine import PricingEngine
from qtmodel.pricingengines.vanilla.analyticeuropeanengine import AnalyticEuropeanEngine
from qtmodel.pricingengines.vanilla.binomialengine import BinomialVanillaEngine
from qtmodel.pricingengines.vanilla.fdblackscholesvanillaengine import FdBlackScholesVanillaEngine
from qtmodel.pricingengines.vanilla.integralengine import IntegralEngine
from qtmodel.processes.blackscholesprocess import BlackScholesMertonProcess, BlackScholesProcess
from qtmodel.quote import Quote
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.settings import Settings, SavedSettings
from qtmodel.termstructures.volatility.equityfx.blackvoltermstructure import BlackVolTermStructure
from qtmodel.termstructures.yieldtermstructure import YieldTermStructure
from qtmodel.time.calendars.target import TARGET
from qtmodel.time.date import DateTool
from qtmodel.time.daycounters.actual360 import Actual360
from qtmodel.time.daycounters.actual365fixed import Actual365Fixed
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.types import Real
from utilities import exercise_type_to_string, payoff_type_to_string, flat_rate, flat_vol, time_to_days, relative_error, \
    Flag


def report_failure(greek_name, payoff, exercise, s, q, r, today, v, expected, calculated, error, tolerance):
    raise QTError(f"{exercise_type_to_string(exercise)} {payoff.option_type()} option with \
               {payoff_type_to_string(payoff)} payoff:\n\
               spot value: {s} \n \
               strike:{payoff.strike()}\n\
               dividend yield: {q:.4%}\n\
               risk-free rate: {r:.4%} \n\
               reference date: {today}\n\
               maturity: {exercise.last_date()}\n\
               volatility: {v:.4%} \n\
               expected {greek_name}:{expected}\n\
               calculated {greek_name}:{calculated}\n\
               error: {error}\n\
               tolerance:{tolerance}")


class EuropeanOptionData:

    def __init__(self, option_type: OptionTypes = None, strike: Real = None, s: Real = None, q: Real = None,
                 r: Real = None, t: Real = None, v: Real = None, result: Real = None, tol: Real = None):
        self.type = option_type
        self.strike = strike
        self.s = s
        self.q = q
        self.r = r
        self.t = t
        self.v = v
        self.result = result
        self.tol = tol


class EngineType(Enum):
    Analytic = 0
    JR = 1
    CRR = 2
    EQP = 3
    TGEO = 4
    TIAN = 5
    LR = 6
    JOSHI = 7
    FiniteDifferences = 8
    Integral = 9
    PseudoMonteCarlo = 10
    QuasiMonteCarlo = 11
    FFT = 12


def make_process(u, q, r, vol):
    return BlackScholesMertonProcess(Handle(u), Handle(q), Handle(r), Handle(vol))


def make_option(payoff, exercise, u, q, r, vol, engine_type, binomial_steps, samples):
    stoch_process = make_process(u, q, r, vol)

    engine = ()
    if engine_type == EngineType.Analytic:
        engine = AnalyticEuropeanEngine(stoch_process)
    elif engine_type == EngineType.JR:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, JarrowRudd)
    elif engine_type == EngineType.CRR:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, CoxRossRubinstein)
    elif engine_type == EngineType.EQP:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, AdditiveEQPBinomialTree)
    elif engine_type == EngineType.TGEO:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, Trigeorgis)
    elif engine_type == EngineType.TIAN:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, Tian)
    elif engine_type == EngineType.LR:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, LeisenReimer)
    elif engine_type == EngineType.JOSHI:
        engine = BinomialVanillaEngine(stoch_process, binomial_steps, Joshi4)
    elif engine_type == EngineType.FiniteDifferences:
        engine = FdBlackScholesVanillaEngine(process=stoch_process, t_grid=binomial_steps, x_grid=samples)
    elif engine_type == EngineType.Integral:
        engine = IntegralEngine(stoch_process)
    # elif engine_type == EngineType.PseudoMonteCarlo:
    #     engine = MakeMCEuropeanEngine < PseudoRandom > (stoch_process).with_steps(1).with_samples(samples).withSeed(42)
    # elif engine_type == EngineType.QuasiMonteCarlo:
    #     engine = MakeMCEuropeanEngine < LowDiscrepancy > (stoch_process).with_steps(1).with_samples(samples)
    # elif engine_type == EngineType.FFT:
    #     engine = FFTVanillaEngine(stoch_process))
    else:
        raise QTError("unknown engine type")

    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    return option


def test_values():
    print("Testing European option values...")

    backup = SavedSettings()

    #     The data below are from
    #       "Option pricing formulas", E.G. Haug, McGraw-Hill 1998
    #
    values = [EuropeanOptionData(OptionTypes.Call, 65.00, 60.00, 0.00, 0.08, 0.25, 0.30, 2.1334, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 95.00, 100.00, 0.05, 0.10, 0.50, 0.20, 2.4648, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 19.00, 19.00, 0.10, 0.10, 0.75, 0.28, 1.7011, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 19.00, 19.00, 0.10, 0.10, 0.75, 0.28, 1.7011, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 1.60, 1.56, 0.08, 0.06, 0.50, 0.12, 0.0291, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 70.00, 75.00, 0.05, 0.10, 0.50, 0.35, 4.0870, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.10, 0.15, 0.0205, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.10, 0.15, 1.8734, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.10, 0.15, 9.9413, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.10, 0.25, 0.3150, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.10, 0.25, 3.1217, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.10, 0.25, 10.3556, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.10, 0.35, 0.9474, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.10, 0.35, 4.3693, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.10, 0.35, 11.1381, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.50, 0.15, 0.8069, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.50, 0.15, 4.0232, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.50, 0.15, 10.5769, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.50, 0.25, 2.7026, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.50, 0.25, 6.6997, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.50, 0.25, 12.7857, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 90.00, 0.10, 0.10, 0.50, 0.35, 4.9329, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 100.00, 0.10, 0.10, 0.50, 0.35, 9.3679, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 100.00, 110.00, 0.10, 0.10, 0.50, 0.35, 15.3086, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.10, 0.15, 9.9210, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.10, 0.15, 1.8734, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.10, 0.15, 0.0408, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.10, 0.25, 10.2155, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.10, 0.25, 3.1217, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.10, 0.25, 0.4551, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.10, 0.35, 10.8479, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.10, 0.35, 4.3693, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.10, 0.35, 1.2376, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.50, 0.15, 10.3192, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.50, 0.15, 4.0232, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.50, 0.15, 1.0646, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.50, 0.25, 12.2149, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.50, 0.25, 6.6997, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.50, 0.25, 3.2734, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 90.00, 0.10, 0.10, 0.50, 0.35, 14.4452, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 100.00, 0.10, 0.10, 0.50, 0.35, 9.3679, 1.0e-4),
              EuropeanOptionData(OptionTypes.Put, 100.00, 110.00, 0.10, 0.10, 0.50, 0.35, 5.7963, 1.0e-4),
              EuropeanOptionData(OptionTypes.Call, 40.00, 42.00, 0.08, 0.04, 0.75, 0.35, 5.0975, 1.0e-4)]
    dc = Actual360()
    today = datetime.today()

    spot = SimpleQuote(0.0)
    q_rate = SimpleQuote(0.0)
    q_ts = flat_rate(today, q_rate, dc)
    r_rate = (SimpleQuote(0.0))
    r_ts = flat_rate(today, r_rate, dc)
    vol = (SimpleQuote(0.0))
    vol_ts = flat_vol(today, vol, dc)

    for value in values:

        payoff = (PlainVanillaPayoff(value.type, value.strike))
        ex_date = DateTool.advance(date=today, n=time_to_days(value.t), units=TimeUnit.Days)
        exercise = (EuropeanExercise(ex_date))

        spot.set_value(value.s)
        q_rate.set_value(value.q)
        r_rate.set_value(value.r)
        vol.set_value(value.v)

        stoch_process = (
            BlackScholesMertonProcess(x0=Handle(spot), dividend_ts=Handle(q_ts), risk_free_ts=Handle(r_ts),
                                      black_vol_ts=Handle(vol_ts)))

        engine = AnalyticEuropeanEngine(stoch_process)

        option = EuropeanOption(payoff, exercise)
        option.set_pricing_engine(engine)

        calculated = option.NPV()
        error = abs(calculated - value.result)
        tolerance = value.tol
        if error > tolerance:
            report_failure("value", payoff, exercise, value.s, value.q, value.r, today, value.v, value.result,
                           calculated, error, tolerance)

        engine = FdBlackScholesVanillaEngine(process=stoch_process, t_grid=200, x_grid=400)
        option.set_pricing_engine(engine)

        calculated = option.NPV()
        error = abs(calculated - value.result)
        tolerance = 1.0e-3
        if error > tolerance:
            report_failure("value", payoff, exercise, value.s, value.q, value.r, today, value.v, value.result,
                           calculated, error, tolerance)


def test_greek_values():
    print("Testing European option greek values...")

    backup = SavedSettings()

    #     The data below are from
    #       "Option pricing formulas", E.G. Haug, McGraw-Hill 1998
    #       pag 11-16
    #
    values = [EuropeanOptionData(OptionTypes.Call, 100.00, 105.00, 0.10, 0.10, 0.500000, 0.36, 0.5946, 0),
              EuropeanOptionData(OptionTypes.Put, 100.00, 105.00, 0.10, 0.10, 0.500000, 0.36, -0.3566, 0),
              EuropeanOptionData(OptionTypes.Put, 100.00, 105.00, 0.10, 0.10, 0.500000, 0.36, -4.8775, 0),
              EuropeanOptionData(OptionTypes.Call, 60.00, 55.00, 0.00, 0.10, 0.750000, 0.30, 0.0278, 0),
              EuropeanOptionData(OptionTypes.Put, 60.00, 55.00, 0.00, 0.10, 0.750000, 0.30, 0.0278, 0),
              EuropeanOptionData(OptionTypes.Call, 60.00, 55.00, 0.00, 0.10, 0.750000, 0.30, 18.9358, 0),
              EuropeanOptionData(OptionTypes.Put, 60.00, 55.00, 0.00, 0.10, 0.750000, 0.30, 18.9358, 0),
              EuropeanOptionData(OptionTypes.Put, 405.00, 430.00, 0.05, 0.07, 1.0 / 12.0, 0.20, -31.1924, 0),
              EuropeanOptionData(OptionTypes.Put, 405.00, 430.00, 0.05, 0.07, 1.0 / 12.0, 0.20, -0.0855, 0),
              EuropeanOptionData(OptionTypes.Call, 75.00, 72.00, 0.00, 0.09, 1.000000, 0.19, 38.7325, 0),
              EuropeanOptionData(OptionTypes.Put, 490.00, 500.00, 0.05, 0.08, 0.250000, 0.15, 42.2254, 0)]

    dc = Actual360()
    today = datetime.today()
    spot = SimpleQuote(0.0)
    q_rate = SimpleQuote(0.0)
    q_ts = flat_rate(today, q_rate, dc)
    r_rate = SimpleQuote(0.0)
    r_ts = flat_rate(today, r_rate, dc)
    vol = SimpleQuote(0.0)
    vol_ts = flat_vol(today, vol, dc)
    stoch_process = (
        BlackScholesMertonProcess(Handle(spot), Handle(q_ts), Handle(r_ts), Handle(vol_ts)))
    engine = AnalyticEuropeanEngine(stoch_process)

    i = -1

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.delta()
    error = abs(calculated - values[i].result)
    tolerance = 1e-4
    if error > tolerance:
        report_failure("delta", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.delta()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("delta", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.elasticity()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("elasticity", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.gamma()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("gamma", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = (EuropeanExercise(ex_date))
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.gamma()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("gamma", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = (EuropeanExercise(ex_date))
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.vega()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("vega", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.vega()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("vega", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.theta()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("theta", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.theta_per_day()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("thetaPerDay", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = EuropeanExercise(ex_date)
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.rho()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("rho", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)

    i += 1
    payoff = PlainVanillaPayoff(values[i].type, values[i].strike)
    ex_date = DateTool.advance(date=today, n=time_to_days(values[i].t), units=TimeUnit.Days)
    exercise = (EuropeanExercise(ex_date))
    spot.set_value(values[i].s)
    q_rate.set_value(values[i].q)
    r_rate.set_value(values[i].r)
    vol.set_value(values[i].v)
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine)
    calculated = option.dividend_rho()
    error = abs(calculated - values[i].result)
    if error > tolerance:
        report_failure("dividendRho", payoff, exercise, values[i].s, values[i].q, values[i].r, today, values[i].v,
                       values[i].result, calculated, error, tolerance)


def test_greeks():
    print("Testing analytic European option greeks...")

    backup = SavedSettings()

    calculated = {}
    expected = {}
    tolerance = {}
    tolerance["delta"] = 1.0e-5
    tolerance["gamma"] = 1.0e-5
    tolerance["theta"] = 1.0e-5
    tolerance["rho"] = 1.0e-5
    tolerance["div_rho"] = 1.0e-5
    tolerance["vega"] = 1.0e-5

    types = [OptionTypes.Call, OptionTypes.Put]
    strikes = [50.0, 99.5, 100.0, 100.5, 150.0]
    underlyings = [100.0]
    q_rates = [0.04, 0.05, 0.06]
    r_rates = [0.01, 0.05, 0.15]
    residual_times = [1.0, 2.0]
    vols = [0.11, 0.50, 1.20]

    dc = Actual360()
    today = datetime.today()
    Settings().evaluation_date = today

    spot = SimpleQuote(0.0)
    q_rate = SimpleQuote(0.0)
    q_ts = Handle(flat_rate(forward=q_rate, dc=dc))
    r_rate = SimpleQuote(0.0)
    r_ts = Handle(flat_rate(forward=r_rate, dc=dc))
    vol = SimpleQuote(0.0)
    vol_ts = Handle(flat_vol(vol=vol, dc=dc))

    payoff = ()

    for type in types:
        for strike in strikes:
            for residual_time in residual_times:
                ex_date = DateTool.advance(date=today, n=time_to_days(residual_time), units=TimeUnit.Days)
                exercise = (EuropeanExercise(ex_date))
                for kk in range(0, 3):
                    # option to check
                    if kk == 0:
                        payoff = PlainVanillaPayoff(type, strike)
                    elif kk == 1:
                        payoff = CashOrNothingPayoff(type, strike, 100.0)
                    elif kk == 2:
                        payoff = AssetOrNothingPayoff(type, strike)
                    elif kk == 3:
                        payoff = GapPayoff(type, strike, 100.0)

                    stoch_process = BlackScholesMertonProcess(Handle(spot), q_ts, r_ts, vol_ts)
                    engine = AnalyticEuropeanEngine(stoch_process)
                    option = EuropeanOption(payoff, exercise)
                    option.set_pricing_engine(engine)

                    for u in underlyings:
                        for m in q_rates:
                            for n in r_rates:
                                for v in vols:
                                    q = m
                                    r = n
                                    spot.set_value(u)
                                    q_rate.set_value(q)
                                    r_rate.set_value(r)
                                    vol.set_value(v)

                                    value = option.NPV()
                                    calculated["delta"] = option.delta()
                                    calculated["gamma"] = option.gamma()
                                    calculated["theta"] = option.theta()
                                    calculated["rho"] = option.rho()
                                    calculated["div_rho"] = option.dividend_rho()
                                    calculated["vega"] = option.vega()

                                    if value > spot.value() * 1.0e-5:
                                        # perturb spot and get delta and gamma
                                        du = u * 1.0e-4
                                        spot.set_value(u + du)
                                        value_p = option.NPV()
                                        delta_p = option.delta()
                                        spot.set_value(u - du)
                                        value_m = option.NPV()
                                        delta_m = option.delta()
                                        spot.set_value(u)
                                        expected["delta"] = (value_p - value_m) / (2 * du)
                                        expected["gamma"] = (delta_p - delta_m) / (2 * du)

                                        # perturb rates and get rho and dividend rho
                                        dr = r * 1.0e-4
                                        r_rate.set_value(r + dr)
                                        value_p = option.NPV()
                                        r_rate.set_value(r - dr)
                                        value_m = option.NPV()
                                        r_rate.set_value(r)
                                        expected["rho"] = (value_p - value_m) / (2 * dr)

                                        dq = q * 1.0e-4
                                        q_rate.set_value(q + dq)
                                        value_p = option.NPV()
                                        q_rate.set_value(q - dq)
                                        value_m = option.NPV()
                                        q_rate.set_value(q)
                                        expected["div_rho"] = (value_p - value_m) / (2 * dq)

                                        # perturb volatility and get vega
                                        dv = v * 1.0e-4
                                        vol.set_value(v + dv)
                                        value_p = option.NPV()
                                        vol.set_value(v - dv)
                                        value_m = option.NPV()
                                        vol.set_value(v)
                                        expected["vega"] = (value_p - value_m) / (2 * dv)

                                        # perturb date and get theta
                                        d_t = dc.year_fraction(today + timedelta(days=-1), today + timedelta(days=1))
                                        Settings().evaluation_date = today + timedelta(days=-1)
                                        value_m = option.NPV()
                                        Settings().evaluation_date = today + timedelta(days=1)
                                        value_p = option.NPV()
                                        Settings().evaluation_date = today
                                        expected["theta"] = (value_p - value_m) / d_t

                                        # compare
                                        for key in calculated:
                                            expct = expected[key]
                                            calcl = calculated[key]
                                            tol = tolerance[key]
                                            error = relative_error(expct, calcl, u)
                                            if error > tol:
                                                report_failure(key, payoff, exercise, u, q, r, today, v, expct, calcl,
                                                               error, tol)


def test_implied_vol():
    print("Testing European option implied volatility...")

    backup = SavedSettings()

    max_evaluations = 100
    tolerance = 1.0e-6

    # test options
    types = [OptionTypes.Call, OptionTypes.Put]
    strikes = [90.0, 99.5, 100.0, 100.5, 110.0]
    lengths = [36, 180, 360, 1080]

    # test data
    underlyings = [90.0, 95.0, 99.9, 100.0, 100.1, 105.0, 110.0]
    q_rates = [0.01, 0.05, 0.10]
    r_rates = [0.01, 0.05, 0.10]
    vols = [0.01, 0.20, 0.30, 0.70, 0.90]

    dc = Actual360()
    today = datetime.today()

    spot = SimpleQuote(0.0)
    vol = SimpleQuote(0.0)
    vol_ts = flat_vol(today, vol, dc)
    q_rate = SimpleQuote(0.0)
    q_ts = flat_rate(today, q_rate, dc)
    r_rate = SimpleQuote(0.0)
    r_ts = flat_rate(today, r_rate, dc)

    for type in types:
        for strike in strikes:
            for length in lengths:
                # option to check
                ex_date = DateTool.advance(date=today, n=length, units=TimeUnit.Days)
                exercise = EuropeanExercise(ex_date)
                payoff = PlainVanillaPayoff(type, strike)
                option = make_option(payoff, exercise, spot, q_ts, r_ts, vol_ts, EngineType.Analytic, None, None)

                process = make_process(spot, q_ts, r_ts, vol_ts)

                for u in underlyings:
                    for m in q_rates:
                        for n in r_rates:
                            for v in vols:
                                q = m
                                r = n
                                spot.set_value(u)
                                q_rate.set_value(q)
                                r_rate.set_value(r)
                                vol.set_value(v)

                                value = option.NPV()
                                impl_vol = 0.0  # just to remove a warning...
                                if value != 0.0:
                                    # shift guess somehow
                                    vol.set_value(v * 0.5)
                                    if abs(value - option.NPV()) <= 1.0e-12:
                                        # flat price vs vol --- pointless (and
                                        # numerically unstable) to solve
                                        continue
                                    try:
                                        impl_vol = option.implied_volatility(value, process, tolerance, max_evaluations)
                                    except Exception as e:
                                        raise QTError(
                                            f"\nimplied vol calculation failed:\n  option: {type} \n   strike:"
                                            f" {strike} \n   spot value: {u} \n   dividend yield: {q:.4%} \n "
                                            f"  risk-free rate: {r:.4%} \n today: {today} \n  maturity: {ex_date} \n"
                                            f"   volatility: {v:.4%} \n   option value: {value} \n {e}")
                                    if abs(impl_vol - v) > tolerance:
                                        # the difference might not matter
                                        vol.set_value(impl_vol)
                                        value2 = option.NPV()
                                        error = relative_error(value, value2, u)
                                        if error > tolerance:
                                            raise QTError(
                                                f"type  option :\n    spot value: {u} \n strike: {strike} \n"
                                                f"dividend yield: {q:.4%}) \n risk-free rate:{r:.4%} \n maturity: {ex_date} \n"
                                                f"original volatility: {v:.4%} \n price: {value} \n implied volatility: "
                                                f"{impl_vol:.4%}) \n corresponding price: {value2} \n error: {error}")


def test_implied_vol_containment():
    print("Testing -containment of implied volatility calculation...")

    backup = SavedSettings()

    max_evaluations = 100
    tolerance = 1.0e-6

    # test options

    dc = Actual360()
    today = datetime.today()

    spot = SimpleQuote(100.0)
    underlying = Handle(spot)
    q_rate = SimpleQuote(0.05)
    q_ts = Handle(flat_rate(today, q_rate, dc))
    r_rate = SimpleQuote(0.03)
    r_ts = Handle(flat_rate(today, r_rate, dc))
    vol = SimpleQuote(0.20)
    vol_ts = Handle(flat_vol(today, vol, dc))

    exercise_date = DateTool.advance(date=today, n=1, units=TimeUnit.Years)
    exercise = EuropeanExercise(exercise_date)
    payoff = PlainVanillaPayoff(OptionTypes.Call, 100.0)

    process = BlackScholesMertonProcess(underlying, q_ts, r_ts, vol_ts)
    engine = AnalyticEuropeanEngine(process)
    # link to the same stochastic process, which shouldn't be changed
    # by calling methods of either option

    option1 = EuropeanOption(payoff, exercise)
    option1.set_pricing_engine(engine)
    option2 = EuropeanOption(payoff, exercise)
    option2.set_pricing_engine(engine)

    # test

    ref_value = option2.NPV()

    f = Flag()
    f.register_with(option2)

    option1.implied_volatility(ref_value * 1.5, process, tolerance, max_evaluations)

    if f.is_up():
        raise QTError("implied volatility calculation triggered a change in another instrument")

    option2.recalculate()
    if abs(option2.NPV() - ref_value) >= 1.0e-8:
        raise QTError(
            f"implied volatility calculation changed the value of another instrument: \n previous value: {ref_value:.8%}"
            f" \n current value: {option2.NPV()}")

    vol.set_value(vol.value() * 1.5)

    if not f.is_up():
        raise QTError("volatility change not notified")

    if abs(option2.NPV() - ref_value) <= 1.0e-8:
        raise QTError("volatility change did not cause the value to change")

    # different engines


def check_engine_consistency(engine, binomial_steps, samples, tolerance, test_greeks=False):
    calculated = {}
    expected = {}

    # test options
    types = [OptionTypes.Call, OptionTypes.Put]
    strikes = [75.0, 100.0, 125.0]
    lengths = [1]

    # test data
    underlyings = [100.0]
    q_rates = [0.00, 0.05]
    r_rates = [0.01, 0.05, 0.15]
    vols = [0.11, 0.50, 1.20]

    dc = Actual360()
    today = datetime.today()

    spot = SimpleQuote(0.0)
    vol = (SimpleQuote(0.0))
    vol_ts = flat_vol(today, vol, dc)
    q_rate = (SimpleQuote(0.0))
    q_ts = flat_rate(today, q_rate, dc)
    r_rate = (SimpleQuote(0.0))
    r_ts = flat_rate(today, r_rate, dc)

    for type in types:
        for strike in strikes:
            for length in lengths:
                ex_date = today + timedelta(days=length * 360)
                exercise = EuropeanExercise(ex_date)
                payoff = PlainVanillaPayoff(type, strike)
                # reference option
                ref_option = make_option(payoff, exercise, spot, q_ts, r_ts, vol_ts, EngineType.Analytic, None, None)
                # option to check
                option = make_option(payoff, exercise, spot, q_ts, r_ts, vol_ts, engine, binomial_steps, samples)

                for u in underlyings:
                    for m in q_rates:
                        for n in r_rates:
                            for v in vols:
                                q = m
                                r = n
                                spot.set_value(u)
                                q_rate.set_value(q)
                                r_rate.set_value(r)
                                vol.set_value(v)

                                expected.clear()
                                calculated.clear()

                                # FLOATING_POINT_EXCEPTION
                                expected["value"] = ref_option.NPV()
                                calculated["value"] = option.NPV()

                                if test_greeks and option.NPV() > spot.value() * 1.0e-5:
                                    expected["delta"] = ref_option.delta()
                                    expected["gamma"] = ref_option.gamma()
                                    expected["theta"] = ref_option.theta()
                                    calculated["delta"] = option.delta()
                                    calculated["gamma"] = option.gamma()
                                    calculated["theta"] = option.theta()
                                for key in calculated:
                                    expct = expected[key]
                                    calcl = calculated[key]
                                    tol = tolerance[key]
                                    error = relative_error(expct, calcl, u)
                                    if error > tol:
                                        report_failure(key, payoff, exercise, u, q, r, today, v, expct, calcl,
                                                       error, tol)


def test_jrbinomial_engines():
    print("Testing JR binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.JR
    steps = 251
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.002
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_crrbinomial_engines():
    print("Testing CRR binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.CRR
    steps = 501
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.02
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_eqpbinomial_engines():
    print("Testing EQP binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.EQP
    steps = 501
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.02
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_tgeobinomial_engines():
    print("Testing TGEO binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.TGEO
    steps = 251
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.002
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_tianbinomial_engines():
    print("Testing TIAN binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.TIAN
    steps = 251
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.002
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_lrbinomial_engines():
    print("Testing LR binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.LR
    steps = 251
    samples = None
    relative_tol = {}
    relative_tol["value"] = 1.0e-6
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_joshibinomial_engines():
    print("Testing Joshi binomial European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.JOSHI
    steps = 251
    samples = None
    relative_tol = {}
    relative_tol["value"] = 1.0e-7
    relative_tol["delta"] = 1.0e-3
    relative_tol["gamma"] = 1.0e-4
    relative_tol["theta"] = 0.03
    check_engine_consistency(engine, steps, samples, relative_tol, True)


def test_fd_engines():
    print("Testing finite-difference European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.FiniteDifferences
    time_steps = 500
    grid_points = 500
    relative_tol = {}
    relative_tol["value"] = 1.0e-4
    relative_tol["delta"] = 1.0e-6
    relative_tol["gamma"] = 1.0e-6
    relative_tol["theta"] = 1.0e-3
    check_engine_consistency(engine, time_steps, grid_points, relative_tol, True)


def test_integral_engines():
    print("Testing integral engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.Integral
    time_steps = 300
    grid_points = 300
    relative_tol = {}
    relative_tol["value"] = 0.0001
    check_engine_consistency(engine, time_steps, grid_points, relative_tol)


def test_mc_engines():
    print("Testing Monte Carlo European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.PseudoMonteCarlo
    steps = None
    samples = 40000
    relative_tol = {}
    relative_tol["value"] = 0.01
    check_engine_consistency(engine, steps, samples, relative_tol)


def test_qmc_engines():
    print("Testing Quasi Monte Carlo European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.QuasiMonteCarlo
    steps = None
    samples = 4095  # 2^12-1
    relative_tol = {}
    relative_tol["value"] = 0.01
    check_engine_consistency(engine, steps, samples, relative_tol)


def test_fftengines():
    print("Testing FFT European engines against analytic results...")

    backup = SavedSettings()

    engine = EngineType.FFT
    steps = None
    samples = None
    relative_tol = {}
    relative_tol["value"] = 0.01
    check_engine_consistency(engine, steps, samples, relative_tol)


# def test_local_volatility():
#     print("Testing finite-differences with local volatility...")
#
#     backup = SavedSettings()
#
#     settlement_date = datetime(2002, 7, 5)
#     Settings().evaluationDate = settlement_date
#
#     day_counter = Actual365Fixed()
#     calendar = TARGET()
#
#     t = [13, 41, 75, 165, 256, 345, 524, 703]
#     r = [0.0357, 0.0349, 0.0341, 0.0355, 0.0359, 0.0368, 0.0386, 0.0401]
#
#     rates = [1, 0.0357]
#     dates = [1, settlement_date]
#     for i in range(0, 7):
#         dates.append(settlement_date + timedelta(days=t[i]))
#         rates.append(r[i])
#     r_ts = ZeroCurve(dates, rates, day_counter)
#     q_ts = flat_rate(settlement_date, 0.0, day_counter)
#
#     s0 = (SimpleQuote(4500.00))
#
#     strikes = [100, 500, 2000, 3400, 3600, 3800, 4000, 4200, 4400, 4500, 4600, 4800, 5000, 5200, 5400, 5600, 7500,
#                10000, 20000, 30000]
#
#     v = [1.015873, 1.015873, 1.015873, 0.89729, 0.796493, 0.730914, 0.631335, 0.568895, 0.711309, 0.711309,
#          0.711309, 0.641309, 0.635593, 0.583653, 0.508045, 0.463182, 0.516034, 0.500534, 0.500534, 0.500534,
#          0.448706, 0.416661, 0.375470, 0.353442, 0.516034, 0.482263, 0.447713, 0.387703, 0.355064, 0.337438,
#          0.316966, 0.306859, 0.497587, 0.464373, 0.430764, 0.374052, 0.344336, 0.328607, 0.310619, 0.301865,
#          0.479511, 0.446815, 0.414194, 0.361010, 0.334204, 0.320301, 0.304664, 0.297180, 0.461866, 0.429645,
#          0.398092, 0.348638, 0.324680, 0.312512, 0.299082, 0.292785, 0.444801, 0.413014, 0.382634, 0.337026,
#          0.315788, 0.305239, 0.293855, 0.288660, 0.428604, 0.397219, 0.368109, 0.326282, 0.307555, 0.298483,
#          0.288972, 0.284791, 0.420971, 0.389782, 0.361317, 0.321274, 0.303697, 0.295302, 0.286655, 0.282948,
#          0.413749, 0.382754, 0.354917, 0.316532, 0.300016, 0.292251, 0.284420, 0.281164, 0.400889, 0.370272,
#          0.343525, 0.307904, 0.293204, 0.286549, 0.280189, 0.277767, 0.390685, 0.360399, 0.334344, 0.300507,
#          0.287149, 0.281380, 0.276271, 0.274588, 0.383477, 0.353434, 0.327580, 0.294408, 0.281867, 0.276746,
#          0.272655, 0.271617, 0.379106, 0.349214, 0.323160, 0.289618, 0.277362, 0.272641, 0.269332, 0.268846,
#          0.377073, 0.347258, 0.320776, 0.286077, 0.273617, 0.269057, 0.266293, 0.266265, 0.399925, 0.369232,
#          0.338895, 0.289042, 0.265509, 0.255589, 0.249308, 0.249665, 0.423432, 0.406891, 0.373720, 0.314667,
#          0.281009, 0.263281, 0.246451, 0.242166, 0.453704, 0.453704, 0.453704, 0.381255, 0.334578, 0.305527,
#          0.268909, 0.251367, 0.517748, 0.517748, 0.517748, 0.416577, 0.364770, 0.331595, 0.287423, 0.264285]
#
#     black_vol_matrix = pd.DataFrame(len(strikes), len(dates) - 1)
#     i = 0
#     while i < len(strikes):
#         j = 1
#         while j < len(dates):
#             black_vol_matrix[i][j - 1] = v[i * (len(dates) - 1) + j - 1]
#             j += 1
#         i += 1
#
#     vol_ts = (
#         BlackVarianceSurface(settlement_date, calendar, list(dates.begin() + 1, dates.end()), strikes,
#                              black_vol_matrix, day_counter))
#     vol_ts.setInterpolation < Bicubic > ()
#     process = make_process(s0, q_ts, r_ts, vol_ts)
#
#     scheme_descs = [(FdmSchemeDesc.douglas(), "Douglas"), (FdmSchemeDesc.crank_nicolson(), "Crank-Nicolson"),
#                     (FdmSchemeDesc.modified_craig_sneyd(), "Mod. Craig-Sneyd")]
#
#     i = 2
#     while i < len(dates):
#         j = 3
#         while j < len(strikes) - 5:
#             ex_date = dates[i]
#             payoff = (PlainVanillaPayoff(OptionTypes.Call, strikes[j]))
#
#             exercise = (EuropeanExercise(ex_date))
#
#             option = EuropeanOption(payoff, exercise)
#             option.set_pricing_engine( < PricingEngine > (AnalyticEuropeanEngine(process)))
#
#             tol = 0.001
#             expected_npv = option.NPV()
#             expected_delta = option.delta()
#             expected_gamma = option.gamma()
#
#             option.set_pricing_engine(FdBlackScholesVanillaEngine(process, 200, 400))
#
#             calculated_npv = option.NPV()
#             calculated_delta = option.delta()
#             calculated_gamma = option.gamma()
#
#             # check implied pricing first
#             if abs(expected_npv - calculated_npv) > tol * expected_npv:
#                 raise QTError(
#                     f"Failed to reproduce option price for \n strike: {payoff.strike()} \n maturity: {ex_date}\n"
#                     f"calculated:{calculated_npv}\n expected: {expected_npv}")
#             if abs(expected_delta - calculated_delta) > tol * expected_delta:
#                 raise QTError(
#                     f"Failed to reproduce option delta for \n strike: {payoff.strike()}\n maturity: {ex_date}\n"
#                     f"calculated: {calculated_delta}\n expected: {expected_delta}")
#             if abs(expected_gamma - calculated_gamma) > tol * expected_gamma:
#                 raise QTError(
#                     f"Failed to reproduce option gamma for \n strike: {payoff.strike()}\n maturity: {ex_date}\n"
#                     f"calculated: {calculated_gamma}\n expected: {expected_gamma}")
#
#             # check local vol pricing
#             # delta/gamma are not the same by definition (model implied greeks)
#             for scheme_desc in scheme_descs:
#                 option.set_pricing_engine(ext.make_shared < FdBlackScholesVanillaEngine > (
#                     process, 25, 100, 0, scheme_desc[0], True, 0.35))
#
#                 calculated_npv = option.NPV()
#                 if abs(expected_npv - calculated_npv) > tol * expected_npv:
#                     raise QTError(
#                         f"Failed to reproduce local vol option price for \n strike: {payoff.strike()}\n maturity: "
#                         f"{ex_date}\n calculated: {calculated_npv}\n expected: {expected_npv}\n scheme: {scheme_desc[1]}")
#             j += 5
#         i += 2


def test_analytic_engine_discount_curve():
    print("Testing separate discount curve for analytic European engine...")

    backup = SavedSettings()

    dc = Actual360()
    today = datetime.today()

    spot = SimpleQuote(1000.0)
    q_rate = SimpleQuote(0.01)
    q_ts = flat_rate(today, q_rate, dc)
    r_rate = SimpleQuote(0.015)
    r_ts = flat_rate(today, r_rate, dc)
    vol = SimpleQuote(0.02)
    vol_ts = flat_vol(today, vol, dc)
    disc_rate = SimpleQuote(0.015)
    disc_ts = flat_rate(today, disc_rate, dc)

    stoch_process = (
        BlackScholesMertonProcess(Handle(spot), Handle(q_ts), Handle(r_ts), Handle(vol_ts)))
    engine_single_curve = (AnalyticEuropeanEngine(stoch_process))
    engine_multi_curve = (AnalyticEuropeanEngine(stoch_process, Handle(disc_ts)))

    payoff = (PlainVanillaPayoff(OptionTypes.Call, 1025.0))
    ex_date = DateTool.advance(date=today, n=1, units=TimeUnit.Years)
    exercise = (EuropeanExercise(ex_date))
    option = EuropeanOption(payoff, exercise)
    option.set_pricing_engine(engine_single_curve)
    npv_single_curve = option.NPV()
    option.set_pricing_engine(engine_multi_curve)
    npv_multi_curve = option.NPV()
    # check that NPV is the same regardless of engine interface
    qt_ensure(npv_single_curve == npv_multi_curve, "npv_single_curve should equal npv_multi_curve")
    # check that NPV changes if discount rate is changed
    disc_rate.set_value(0.023)
    npv_multi_curve = option.NPV()
    qt_ensure(npv_single_curve != npv_multi_curve, "npv_single_curve should not equal npv_multi_curve")


# def test_pdeschemes():
#     print("Testing different PDE schemes to solve Black-Scholes PDEs...")
#
#     backup = SavedSettings()
#
#     dc = Actual365Fixed()
#     today = datetime(2018, 2, 18)
#
#     Settings().evaluation_date = today
#
#     spot = Handle(100.0)
#     q_ts = Handle(flat_rate(today, 0.06, dc))
#     r_ts = Handle(flat_rate(today, 0.10, dc))
#     vol_ts = Handle(flat_vol(today, 0.35, dc))
#
#     maturity = DateTool.advance(date=today, n=6, units=TimeUnit.Months)
#
#     process = BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)
#
#     analytic = AnalyticEuropeanEngine(process)
#
#     # Crank-Nicolson and Douglas scheme are the same in one dimension
#     douglas = FdBlackScholesVanillaEngine(process, 15, 100, 0, FdmSchemeDesc.douglas())
#
#     crank_nicolson = FdBlackScholesVanillaEngine(process, 15, 100, 0, FdmSchemeDesc.CrankNicolson())
#
#     implicit_euler = FdBlackScholesVanillaEngine(process, 500, 100, 0, FdmSchemeDesc.ImplicitEuler())
#
#     explicit_euler = FdBlackScholesVanillaEngine(process, 1000, 100, 0, FdmSchemeDesc.ExplicitEuler())
#
#     method_of_lines = FdBlackScholesVanillaEngine(process, 1, 100, 0, FdmSchemeDesc.MethodOfLines())
#
#     hundsdorfer = FdBlackScholesVanillaEngine(process, 10, 100, 0, FdmSchemeDesc.hundsdorfer())
#
#     craig_sneyd = FdBlackScholesVanillaEngine(process, 10, 100, 0, FdmSchemeDesc.craig_sneyd())
#
#     mod_craig_sneyd = FdBlackScholesVanillaEngine(process, 15, 100, 0, FdmSchemeDesc.ModifiedCraigSneyd())
#
#     tr_bdf2 = FdBlackScholesVanillaEngine(process, 15, 100, 0, FdmSchemeDesc.tr_bdf_2())
#
#     engines = [(douglas, "Douglas"), (crank_nicolson, "Crank-Nicolson"), (implicit_euler, "Implicit-Euler"),
#                (explicit_euler, "Explicit-Euler"), (method_of_lines, "Method-of-Lines"), (hundsdorfer, "Hundsdorfer"),
#                (craig_sneyd, "Craig-Sneyd"), (mod_craig_sneyd, "Modified Craig-Sneyd"), (tr_bdf2, "TR-BDF2")]
#
#     n_engines = len(engines)
#
#     payoff = PlainVanillaPayoff(OptionTypes.Put, spot.value())
#
#     exercise = EuropeanExercise(maturity)
#
#     option = VanillaOption(payoff, exercise)
#
#     option.set_pricing_engine(analytic)
#     expected = option.NPV()
#
#     tol = 0.006
#
#     for engine in engines:
#         option.set_pricing_engine(engine[0])
#         calculated = option.NPV()
#
#         diff = abs(expected - calculated)
#
#         if diff > tol:
#             raise QTError(f"Failed to reproduce European option values with the {engine[1]} PDE scheme\n calculated: "
#                           f"{calculated}\n expected: {expected}\n difference: {diff}\n  tolerance: {tol}")
#
#         dividend_option = DividendVanillaOption(payoff, exercise,
#                                                 [1, DateTool.advance(date=today, n=3, units=TimeUnit.Months)], [1, 5.0])
#
#         dividend_prices = [None] * n_engines
#         i = 0
#         while i < n_engines:
#             dividend_option.set_pricing_engine(engines[i][1])
#             dividend_prices[i] = dividend_option.NPV()
#             i += 1
#
#         expected_div = std::accumulate(dividend_prices.begin(), dividend_prices.end(), 0.0) / n_engines
#
#         i = 0
#         while i < n_engines:
#             calculated = dividend_prices[i]
#             diff = abs(expected_div - calculated)
#
#             if diff > tol:
#                 raise QTError("Failed to reproduce European option values with dividend and the " << engines[
#                     i].second
#                 PDE
#                 scheme\n
#                 calculated: " << calculated\n    expected: expected_div\n    difference: " << diff\n
#                 tolerance: " << tol)
#                 i += 1
#
#                 # make sure that Douglas and Crank-Nicolson are giving the same result
#                 idx_douglas = std::distance(std::begin(engines), std::find(std::begin(engines), std::end(engines), (
#                     douglas, str("Douglas"))))
#                 douglas_npv = dividend_prices[idx_douglas]
#
#                 idx_crank_nicolson = std::distance(std::begin(engines), std::find(std::begin(engines), std::end(
#                     engines), (
#                                                                                                                 crank_nicolson,
#                                                                                                                 str("Crank-Nicolson"))))
#                 crank_nicolson_npv = dividend_prices[idx_crank_nicolson]
#
#                 scheme_tol = 1e-12
#                 scheme_diff = abs(crank_nicolson_npv - douglas_npv)
#                 if scheme_diff > scheme_tol:
#                 raise QTError(
#                     f"Failed to reproduce Douglas scheme option values with the Crank-Nicolson PDE scheme\n Dougles NPV:{douglas_npv} \n Crank-Nicolson NPV: {crank_nicolson_npv}\n difference: {scheme_diff} \n tolerance:{scheme_tol}")

# def testFdEngineWithNonConstantParameters():
#     print("Testing finite-difference European engine with non-constant parameters...")
#
#     backup = SavedSettings()
#
#     u = 190.0
#     v = 0.20
#
#     dc = Actual360()
#     today = Settings().evaluation_date()
#
#     spot = (SimpleQuote(u))
#     vol_ts = flat_vol(today, v, dc)
#
#     dates = list(5)
#     rates = list(5)
#     dates[0] = today
#     rates[0] = 0.0
#     dates[1] = today + 90
#     rates[1] = 0.001
#     dates[2] = today + 180
#     rates[2] = 0.002
#     dates[3] = today + 270
#     rates[3] = 0.005
#     dates[4] = today + 360
#     rates[4] = 0.01
#     r_ts = ext.make_shared < ForwardCurve > (dates, rates, dc)
#     r = r_ts.zeroRate(dates[4], dc, Continuous)
#
#     process = ext.make_shared < BlackScholesProcess > (
#         Handle < Quote > (spot), Handle < YieldTermStructure > (r_ts), Handle < BlackVolTermStructure > (vol_ts))
#
#     exercise = ext.make_shared < EuropeanExercise > (today + 360)
#     payoff = ext.make_shared < PlainVanillaPayoff > (OptionTypes.Call, 190.0)
#
#     option = EuropeanOption(payoff, exercise)
#
#     option.set_pricing_engine(ext.make_shared < AnalyticEuropeanEngine > (process))
#     expected = option.NPV()
#
#     time_steps = 200
#     grid_points = 201
#     option.set_pricing_engine(ext.make_shared < FdBlackScholesVanillaEngine > (process, time_steps, grid_points))
#     calculated = option.NPV()
#
#     tolerance = 0.01
#     error = abs(expected - calculated)
#     if error > tolerance:
#         report_failure("value", payoff, exercise, u, 0.0, r, today, v, expected, calculated, error, tolerance)
#
#
# def test_douglas_vs_crank_nicolson():
#     print(
#         "Testing Douglas vs Crank-Nicolson scheme for finite-difference European PDE engines...")
#
#     backup = SavedSettings()
#
#     dc = Actual365Fixed()
#     today = datetime(2018, 10, 5)
#
#     Settings().evaluation_date = today
#
#     spot = Handle(ext.make_shared < SimpleQuote > (100.0))
#     q_ts = Handle(flat_rate(today, 0.02, dc))
#     r_ts = Handle(flat_rate(today, 0.075, dc))
#     vol_ts = Handle(flat_vol(today, 0.25, dc))
#
#     process = ext.make_shared < BlackScholesMertonProcess(spot, q_ts, r_ts, vol_ts)
#
#     option = VanillaOption(ext.make_shared < PlainVanillaPayoff > (OptionTypes.Put, spot.value() + 2),
#                            ext.make_shared < EuropeanExercise > (today + Period(6, Months)))
#
#     option.set_pricing_engine(ext.make_shared < AnalyticEuropeanEngine > (process))
#
#     npv = option.NPV()
#     scheme_tol = 1e-12
#     npv_tol = 1e-2
#
#     for theta in range(0.2, 0.81 - 1, 0.1):
#         option.set_pricing_engine(ext.make_shared < FdBlackScholesVanillaEngine > (
#             process, 500, 100, 0, FdmSchemeDesc(FdmSchemeDesc.CrankNicolsonType, theta, 0.0)))
#         crank_nicolson_npv = option.NPV()
#
#         npv_diff = abs(crank_nicolson_npv - npv)
#         if npv_diff > npv_tol:
#             raise QTError(
#                 f"Failed to reproduce european option values with the Crank-Nicolson PDE scheme \n Analytic NPV:{npv}\n  Crank-Nicolson NPV:{crank_nicolson_npv}\n theta: {theta} \n difference: {npv_diff} \n tolerance: {npv_tol}")
#
#         option.set_pricing_engine(ext.make_shared < FdBlackScholesVanillaEngine > (
#             process, 500, 100, 0, FdmSchemeDesc(FdmSchemeDesc.DouglasType, theta, 0.0)))
#         douglas_npv = option.NPV()
#
#         scheme_diff = abs(crank_nicolson_npv - douglas_npv)
#
#         if scheme_diff > scheme_tol:
#             raise QTError(
#                 f"Failed to reproduce Douglas scheme option values with the Crank-Nicolson PDE scheme \n Dougles NPV: {douglas_npv} \n Crank-Nicolson NPV: {crank_nicolson_npv} \n difference: {scheme_diff} \n tolerance: {scheme_tol}")
