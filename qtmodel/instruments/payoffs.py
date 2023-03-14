from qtmodel.error import QTError, qt_require
from qtmodel.option import OptionTypes
from qtmodel.payoff import Payoff
from qtmodel.types import Real


class NullPayoff(Payoff):
    """ Dummy payoff class """

    def name(self):
        return "Null"

    def description(self):
        return self.name()

    def __call__(self, price: Real):
        QTError("dummy payoff given")


class TypePayoff(Payoff):
    """ Intermediate class for put/call payoffs """

    def __init__(self, type: OptionTypes):
        self._type = type

    def option_type(self):
        return self._type

    def description(self):
        return f"{self.name()} {self.option_type()}"


class FloatingTypePayoff(TypePayoff):
    """ Payoff based on a floating strike """

    def __init__(self, type: OptionTypes):
        super(FloatingTypePayoff, self).__init__(type)

    def name(self):
        return "FloatingType"

    def __call__(self, price: Real, strike: Real = None):
        if strike is not None:
            QTError("floating payoff not handled")
        if self._type == OptionTypes.Call:
            return max(price - strike, 0.0)
        elif self._type == OptionTypes.Put:
            return max(strike - price, 0.0)
        else:
            QTError("unknown/illegal option type")


class StrikedTypePayoff(TypePayoff):
    """ Intermediate class for payoffs based on a fixed strike """

    def __init__(self, type: OptionTypes, strike: Real):
        super(StrikedTypePayoff, self).__init__(type)
        self._strike = strike

    def description(self):
        pass

    def strike(self):
        return self._strike


class PlainVanillaPayoff(StrikedTypePayoff):
    """ Plain-vanilla payoff """

    def __init__(self, type: OptionTypes, strike: Real):
        super(PlainVanillaPayoff, self).__init__(type, strike)

    def name(self):
        return "Vanilla"

    def __call__(self, price: Real):
        if self._type == OptionTypes.Call:
            return max(price - self._strike, 0.0)
        elif self._type == OptionTypes.Put:
            return max(self._strike - price, 0.0)
        else:
            raise QTError("unknown/illegal option type")


class PercentageStrikePayoff(StrikedTypePayoff):
    """ Payoff with strike expressed as percentage """

    def __init__(self, type: OptionTypes, moneyness: Real):
        super(PercentageStrikePayoff, self).__init__(type, moneyness)

    def name(self):
        return "PercentageStrike"

    def __call__(self, price: Real):
        if self._type == OptionTypes.Call:
            return price * max(Real(1.0) - self._strike, 0.0)
        elif self._type == OptionTypes.Put:
            return price * max(self._strike - 1.0, 0.0)
        else:
            QTError("unknown/illegal option type")


class AssetOrNothingPayoff(StrikedTypePayoff):
    """
    Definitions of Binary path-independent payoffs used below,
    can be found in M. Rubinstein, E. Reiner:"Unscrambling The Binary Code", Risk, Vol.4 no.9,1991.
    (see: http://www.in-the-money.com/artandpap/Binary%20Options.doc)
    """

    def __init__(self, type: OptionTypes, strike: Real):
        super(AssetOrNothingPayoff, self).__init__(type, strike)

    def name(self):
        return "AssetOrNothing"

    def __call__(self, price: Real):
        if self._type == OptionTypes.Call:
            return price if price - self._strike > 0.0 else 0.0
        elif self._type == OptionTypes.Put:
            return price if self._strike - price > 0.0 else 0.0
        else:
            QTError("unknown/illegal option type")


class CashOrNothingPayoff(StrikedTypePayoff):
    """ Binary cash-or-nothing payoff """

    def __init__(self, type: OptionTypes, strike: Real, cash_payoff: Real):
        super(CashOrNothingPayoff, self).__init__(type, strike)
        self._cash_payoff = cash_payoff

    def name(self):
        return "CashOrNothing"

    def description(self):
        return f"{super().description()}, {self.cash_payoff()} cash payoff"

    def __call__(self, price: Real):
        if self._type == OptionTypes.Call:
            return self._cash_payoff if price - self._strike > 0.0 else 0.0
        elif self._type == OptionTypes.Put:
            return self._cash_payoff if self._strike - price > 0.0 else 0.0
        else:
            QTError("unknown/illegal option type")

    def cash_payoff(self):
        return self._cash_payoff


class GapPayoff(StrikedTypePayoff):
    """
    Binary gap payoff
    This payoff is equivalent to being a) long a PlainVanillaPayoff at
    the first strike (same Call/Put type) and b) short a
    CashOrNothingPayoff at the first strike (same Call/Put type) with
    cash payoff equal to the difference between the second and the first
    strike.
    warning: this payoff can be negative depending on the strikes
    """

    def __init__(self, type: OptionTypes, strike: Real, second_strike: Real):  # a.k.a. payoff strike
        super(GapPayoff, self).__init__(type, strike)
        self._second_strike = second_strike

    def name(self):
        return "Gap"

    def description(self):
        return f" {super().description()}, {self.second_strike()} strike payoff"

    def second_strike(self):
        return self._second_strike

    def __call__(self, price: Real):
        if self._type == OptionTypes.Call:
            return price - self._second_strike if price - self._strike >= 0.0 else 0.0
        elif self._type == OptionTypes.Put:
            return self._second_strike - price if self._strike - price >= 0.0 else 0.0
        else:
            QTError("unknown/illegal option type")


class SuperFundPayoff(StrikedTypePayoff):
    """
    Binary supershare and superfund payoffs

    Binary superfund payoff
    Superfund sometimes also called "supershare", which can lead to ambiguity; within QuantLib
    the terms supershare and superfund are used consistently according to the definitions in
    Bloomberg OVX function's help pages.

    This payoff is equivalent to being (1/lowerstrike) a) long (short) an AssetOrNothing
    Call (Put) at the lower strike and b) short (long) an AssetOrNothing
    Call (Put) at the higher strike
    """

    def __init__(self, strike: Real, second_strike: Real):
        qt_require(strike > 0.0,
                   f"strike ({strike}) must be positive")
        qt_require(second_strike > strike,
                   f"second strike ({second_strike}) must be higher than first strike ({strike})")
        super(SuperFundPayoff, self).__init__(OptionTypes.Call, strike)
        self._second_strike = second_strike

    def name(self):
        return "SuperFund"

    def second_strike(self):
        return self._second_strike

    def __call__(self, price: Real):
        return price / self._strike if (self._strike <= price < self._second_strike) else 0.0


class SuperSharePayoff(StrikedTypePayoff):
    """ Binary supershare payoff """

    def __init__(self, strike: Real, second_strike: Real, cash_payoff: Real):
        qt_require(second_strike > strike,
                   f"second strike ({second_strike}) must be higher than first strike ({strike})")
        super(SuperSharePayoff, self).__init__(OptionTypes.Call, strike)
        self._second_strike = second_strike
        self._cash_payoff = cash_payoff

    def name(self):
        return "SuperShare"

    def description(self):
        return f"{super().description()}, {self.second_strike()} second strike, {self.cash_payoff()} amount"

    def second_strike(self):
        return self._second_strike

    def cash_payoff(self):
        return self._cash_payoff

    def __call__(self, price: Real):
        return self._cash_payoff if (self._strike <= price < self._second_strike) else 0.0
