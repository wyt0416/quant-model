import math

from qtmodel.error import QTError
from qtmodel.exercise import EuropeanExercise, AmericanExercise, BermudanExercise
from qtmodel.handle import Handle
from qtmodel.instruments.payoffs import PlainVanillaPayoff, CashOrNothingPayoff, AssetOrNothingPayoff, SuperSharePayoff, \
    SuperFundPayoff, PercentageStrikePayoff, GapPayoff, FloatingTypePayoff
from qtmodel.patterns.observable import Observer
from qtmodel.quote import Quote
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.volatility.equityfx.blackconstantvol import BlackConstantVol
from qtmodel.termstructures.yield_curve.flatforward import FlatForward
from qtmodel.time.calendars.nullcalendar import NullCalendar
from qtmodel.types import Real


def norm_test(data, h):
    # squared values
    f2 = list(map(lambda i: i ** 2, data))
    # numeric integral of f^2
    i = h * (sum(f2) - 0.5 * f2[0] - 0.5 * f2[len(f2) - 1])
    return math.sqrt(i)


def exercise_type_to_string(h):
    hd = isinstance(h, EuropeanExercise)
    if hd:
        return "European"
    hd = isinstance(h, AmericanExercise)
    if hd:
        return "American"
    hd = isinstance(h, BermudanExercise)
    if hd:
        return "Bermudan"
    else:
        raise QTError("unknown exercise type")


def payoff_type_to_string(h):
    hd = isinstance(h, PlainVanillaPayoff)
    if hd:
        return "plain-vanilla"
    hd = isinstance(h, CashOrNothingPayoff)
    if hd:
        return "cash-or-nothing"
    hd = isinstance(h, AssetOrNothingPayoff)
    if hd:
        return "asset-or-nothing"
    hd = isinstance(h, SuperSharePayoff)
    if hd:
        return "super-share"
    hd = isinstance(h, SuperFundPayoff)
    if hd:
        return "super-fund"
    hd = isinstance(h, PercentageStrikePayoff)
    if hd:
        return "percentage-strike"
    hd = isinstance(h, GapPayoff)
    if hd:
        return "gap"
    hd = isinstance(h, FloatingTypePayoff)
    if hd:
        return "floating-type"
    else:
        raise QTError("unknown payoff type")


def flat_rate(today=None, forward=None, dc=None):
    if today is not None:
        if isinstance(forward, Quote):
            forward = Handle(forward)
            return FlatForward(reference_date=today, forward=forward, day_counter=dc)
        elif isinstance(forward, (int, float)):
            return flat_rate(today=today, forward=SimpleQuote(forward), dc=dc)
    else:
        if isinstance(forward, Quote):
            forward = Handle(forward)
            return FlatForward(settlement_days=0, calendar=NullCalendar(), forward=forward, day_counter=dc)
        elif isinstance(forward, (int, float)):
            return flat_rate(forward=SimpleQuote(forward), dc=dc)


def flat_vol(today=None, vol=None, dc=None):
    if today is not None:
        if isinstance(vol, Quote):
            vol = Handle(vol)
            return BlackConstantVol(reference_date=today, cal=NullCalendar(), volatility=vol, dc=dc)
        elif isinstance(vol, (int, float)):
            return flat_vol(today=today, vol=SimpleQuote(vol), dc=dc)
    else:
        if isinstance(vol, Quote):
            vol = Handle(vol)
            return BlackConstantVol(settlement_days=0, cal=NullCalendar(), volatility=vol, dc=dc)
        elif isinstance(vol, (int, float)):
            return flat_vol(vol=SimpleQuote(vol), dc=dc)


def time_to_days(t: Real, days_per_year: int = 360):
    return round(t * days_per_year)


def relative_error(x1, x2, reference):
    if reference != 0.0:
        return abs(x1 - x2) / reference
    else:
        # fall back to absolute error
        return abs(x1 - x2)


class Flag(Observer):

    def __init__(self):
        super().__init__()
        self._up = None

    def up(self):
        self._up = True

    def lower(self):
        self._up = False

    def is_up(self):
        return self._up

    def update(self):
        self.up()
