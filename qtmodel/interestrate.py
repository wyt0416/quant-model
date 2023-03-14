import math
from datetime import datetime

from qtmodel.compounding import Compounding
from qtmodel.error import qt_require, QTError
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.frequency import Frequency
from qtmodel.types import Real


class InterestRate:
    """
    Concrete interest rate class
    This class encapsulate the interest rate compounding algebra.
    It manages day-counting conventions, compounding conventions,
    conversion between different conventions, discount/compound factor
    calculations, and implied/equivalent rate calculations.
    """

    def __init__(self,
                 r: Real = None,
                 dc: DayCounter = None,
                 comp: Compounding = None,
                 freq: Frequency = None):
        self._r = r
        self._dc = dc
        self._comp = comp
        self._freq_makes_sense = False
        self._freq = None
        if self._comp == Compounding.Compounded or \
                self._comp == Compounding.SimpleThenCompounded or \
                self._comp == Compounding.CompoundedThenSimple:
            self._freq_makes_sense = True
            qt_require(freq != Frequency.Once and freq != Frequency.NoFrequency,
                       "frequency not allowed for this interest rate")
            self._freq = freq.value

    def rate(self):
        return self._r

    def day_counter(self):
        return self._dc

    def compounding(self):
        return self._comp

    def frequency(self):
        return Frequency(int(self._freq)) if self._freq_makes_sense else Frequency.NoFrequency

    def discount_factor(self,
                        t: Real = None,
                        d1: datetime = None,
                        d2: datetime = None,
                        ref_start: datetime = None,
                        ref_end: datetime = None):
        """
        discount/compound factor calculations
        """
        if t is not None:
            return 1.0 / self.compound_factor(t=t)
        elif d1 is not None and d2 is not None:
            qt_require(d2 >= d1, f"d1 ({d1}) later than d2 ({d2})")
            t = self._dc.year_fraction(d1, d2, ref_start, ref_end)
            return self.discount_factor(t=t)
        else:
            raise QTError("if t is not passed, d1 and d2 must be passed")

    def compound_factor(self,
                        t: Real = None,
                        d1: datetime = None,
                        d2: datetime = None,
                        ref_start: datetime = None,
                        ref_end: datetime = None):
        if t is not None:
            qt_require(t >= 0.0, f"negative time ({t}) not allowed")
            qt_require(self._r is not None, "null interest rate")
            if self._comp == Compounding.Simple:
                return 1.0 + self._r * t
            elif self._comp == Compounding.Compounded:
                return math.pow(1.0 + self._r / self._freq, self._freq * t)
            elif self._comp == Compounding.Continuous:
                return math.exp(self._r * t)
            elif self._comp == Compounding.SimpleThenCompounded:
                if t <= 1.0 / Real(self._freq):
                    return 1.0 + self._r * t
                else:
                    return math.pow(1.0 + self._r / self._freq, self._freq * t)
            elif self._comp == Compounding.CompoundedThenSimple:
                if t > 1.0 / Real(self._freq):
                    return 1.0 + self._r * t
                else:
                    return math.pow(1.0 + self._r / self._freq, self._freq * t)
            else:
                QTError("unknown compounding convention")
        elif d1 is not None and d2 is not None:
            qt_require(d2 >= d1, f"d1 ({d1}) later than d2 ({d2})")
            t = self._dc.year_fraction(d1, d2, ref_start, ref_end)
            return self.compound_factor(t=t)
        else:
            raise QTError("if t is not passed, d1 and d2 must be passed")

    @staticmethod
    def implied_rate(compound: Real,
                     result_dc: DayCounter,
                     comp: Compounding,
                     freq: Frequency,
                     t: Real = None,
                     d1: datetime = None,
                     d2: datetime = None,
                     ref_start: datetime = None,
                     ref_end: datetime = None):
        if t is not None:
            qt_require(compound > 0.0, "positive compound factor required")

            if compound == 1.0:
                qt_require(t >= 0.0, f"non negative time ({t}) required")
                r = 0.0
            else:
                qt_require(t > 0.0, f"positive time ({t}) required")
                if comp == Compounding.Simple:
                    r = (compound - 1.0) / t
                elif comp == Compounding.Compounded:
                    r = (math.pow(compound, 1.0 / (freq.value * t)) - 1.0) * freq.value
                elif comp == Compounding.Continuous:
                    r = math.log(compound) / t
                elif comp == Compounding.SimpleThenCompounded:
                    if t <= 1.0 / freq.value:
                        r = (compound - 1.0) / t
                    else:
                        r = (math.pow(compound, 1.0 / (freq.value * t)) - 1.0) * freq.value
                elif comp == Compounding.CompoundedThenSimple:
                    if t > 1.0 / freq.value:
                        r = (compound - 1.0) / t
                    else:
                        r = (math.pow(compound, 1.0 / (freq.value * t)) - 1.0) * freq.value
                else:
                    raise QTError(f"unknown compounding convention ({comp.value})")
            return InterestRate(r, result_dc, comp, freq)
        elif d1 is not None and d2 is not None:
            qt_require(d2 >= d1, f"d1 ({d1}) later than d2 ({d2})")
            t = result_dc.year_fraction(d1, d2, ref_start, ref_end)
            return InterestRate.implied_rate(compound, result_dc, comp, freq, t=t)
        else:
            raise QTError("if t is not passed, d1 and d2 must be passed")

    def equivalent_rate(self,
                        comp: Compounding,
                        freq: Frequency,
                        t: Real = None,
                        result_dc: DayCounter = None,
                        d1: datetime = None,
                        d2: datetime = None,
                        ref_start: datetime = None,
                        ref_end: datetime = None):
        if t is not None:
            return self.implied_rate(compound=self.compound_factor(t=t),
                                     result_dc=self._dc,
                                     comp=comp,
                                     freq=freq,
                                     t=t)
        elif result_dc is not None and d1 is not None and d2 is not None:
            qt_require(d2 >= d1, f"d1 ({d1}) later than d2 ({d2})")
            t1 = self._dc.year_fraction(d1, d2, ref_start, ref_end)
            t2 = result_dc.year_fraction(d1, d2, ref_start, ref_end)
            return self.implied_rate(compound=self.compound_factor(t=t1),
                                     result_dc=result_dc,
                                     comp=comp,
                                     freq=freq,
                                     t=t2)
        else:
            raise QTError("if t is not passed, d1, d2, and result_dc must be passed")

    def __repr__(self):
        if self.rate() is None:
            return "null interest rate"

        _str = f"{self.rate():.2%} {self.day_counter().name()} "
        compounding = self.compounding()
        frequency = self.frequency()
        if compounding == Compounding.Simple:
            _str += "simple compounding"
        elif compounding == Compounding.Compounded:
            if frequency == Frequency.NoFrequency or frequency == Frequency.Once:
                QTError(f"{frequency} frequency not allowed for this interest rate")
            else:
                _str += f"{frequency} compounding"
        elif compounding == Compounding.Continuous:
            _str += "continuous compounding"
        elif compounding == Compounding.SimpleThenCompounded:
            if frequency == Frequency.NoFrequency or frequency == Frequency.Once:
                QTError(f"{frequency} frequency not allowed for this interest rate")
            else:
                _str += f"simple compounding up to {12 / frequency.value} months, then {frequency} compounding"
        elif compounding == Compounding.CompoundedThenSimple:
            if frequency == Frequency.NoFrequency or frequency == Frequency.Once:
                QTError(f"{frequency} frequency not allowed for this interest rate")
            else:
                _str += f"compounding up to {12/frequency.value} months, then {frequency} simple compounding"
        else:
            QTError(f"unknown compounding convention ({self.compounding().value})")

        return _str



