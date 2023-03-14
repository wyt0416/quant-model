import math
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Union

from qtmodel.error import QTError, qt_require, qt_ensure
from qtmodel.termstructures.voltermstructure import VolatilityTermStructure
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendar import Calendar
from qtmodel.time.daycounter import DayCounter
from qtmodel.types import Real


class BlackVolTermStructure(VolatilityTermStructure, metaclass=ABCMeta):
    """
    Black-volatility term structure
    This abstract class defines the interface of concrete
    Black-volatility term structures which will be derived from
    this one.

    Volatilities are assumed to be expressed on an annual basis.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 bdc: BusinessDayConvention = BusinessDayConvention.Following,
                 dc: DayCounter = None):
        super(BlackVolTermStructure, self).__init__(reference_date,
                                                    settlement_days,
                                                    cal,
                                                    bdc,
                                                    dc)

    def black_vol(self,
                  maturity: Union[datetime, Real],
                  strike: Real,
                  extrapolate: bool = False):
        """ spot volatility """
        if isinstance(maturity, datetime):
            self.check_range(d=maturity, extrapolate=extrapolate)
            self.check_strike(strike, extrapolate)
            t = self.time_from_reference(maturity)
            return self.black_vol_impl(t, strike)
        elif isinstance(maturity, (int, float)):
            self.check_range(t=maturity, extrapolate=extrapolate)
            self.check_strike(strike, extrapolate)
            return self.black_vol_impl(maturity, strike)
        else:
            raise QTError("maturity must be datetime or real")

    def black_variance(self,
                       maturity: Union[datetime, Real],
                       strike: Real,
                       extrapolate: bool = False):
        """ spot variance """
        if isinstance(maturity, datetime):
            self.check_range(maturity, extrapolate)
            self.check_strike(strike, extrapolate)
            t = self.time_from_reference(maturity)
            return self.black_variance_impl(t, strike)
        elif isinstance(maturity, (int, float)):
            self.check_range(maturity, extrapolate)
            self.check_strike(strike, extrapolate)
            return self.black_variance_impl(maturity, strike)
        else:
            raise QTError("maturity must be datetime or real")

    def black_forward_vol(self,
                          date1: Union[datetime, Real],
                          date2: Union[datetime, Real],
                          strike: Real,
                          extrapolate: bool = False):
        """ forward (at-the-money) volatility """
        if isinstance(date1, datetime) and isinstance(date2, datetime):
            # (redundant) date-based checks
            qt_require(date1 <= date2,
                       f"{date1} later than {date2}")
            self.check_range(date2, extrapolate)

            # using the time implementation
            time1 = self.time_from_reference(date1)
            time2 = self.time_from_reference(date2)
            return self.black_forward_vol(time1, time2, strike, extrapolate)
        elif isinstance(date1, Real) and isinstance(date2, Real):
            qt_require(date1 <= date2,
                       f"{date1} later than {date2}")
            self.check_range(date2, extrapolate)
            self.check_strike(strike, extrapolate)
            if date2 == date1:
                if date1 == 0.0:
                    epsilon = 1.0e-5
                    var = self.black_variance_impl(epsilon, strike)
                    return math.sqrt(var / epsilon)
                else:
                    epsilon = min(1.0e-5, date1)
                    var1 = self.black_variance_impl(date1 - epsilon, strike)
                    var2 = self.black_variance_impl(date1 + epsilon, strike)
                    qt_ensure(var2 >= var1,
                              "variances must be non-decreasing")
                    return math.sqrt((var2 - var1) / (2 * epsilon))
            else:
                var1 = self.black_variance_impl(date1, strike)
                var2 = self.black_variance_impl(date2, strike)
                qt_ensure(var2 >= var1,
                          "variances must be non-decreasing")
                return math.sqrt((var2 - var1) / (date2 - date1))
        else:
            raise QTError("date must be datetime or real")

    def black_forward_variance(self,
                               date1: Union[datetime, Real],
                               date2: Union[datetime, Real],
                               strike: Real,
                               extrapolate: bool = False):
        """ forward (at-the-money) variance """
        if isinstance(date1, datetime) and isinstance(date2, datetime):
            # (redundant) date-based checks
            qt_require(date1 <= date2,
                       f"{date1} later than {date2}")
            self.check_range(date2, extrapolate)

            # using the time implementation
            time1 = self.time_from_reference(date1)
            time2 = self.time_from_reference(date2)
            return self.black_forward_variance(time1, time2, strike, extrapolate)
        elif isinstance(date1, (int, float)) and isinstance(date2, (int, float)):
            qt_require(date1 <= date2,
                       f"{date1} later than {date2}")
            self.check_range(t=date2, extrapolate=extrapolate)
            self.check_strike(strike, extrapolate)
            v1 = self.black_variance_impl(date1, strike)
            v2 = self.black_variance_impl(date2, strike)
            qt_ensure(v2 >= v1,
                      "variances must be non-decreasing")
            return v2 - v1
        else:
            raise QTError("date must be datetime or real")

    @abstractmethod
    def black_vol_impl(self, t: Real, strike: Real):
        """ Black volatility calculation """
        pass

    @abstractmethod
    def black_variance_impl(self, t: Real, strike: Real):
        """ Black variance calculation """
        pass


class BlackVolatilityTermStructure(BlackVolTermStructure):
    """
    Black-volatility term structure
    This abstract class acts as an adapter to BlackVolTermStructure
    allowing the programmer to implement only the
    black_vol_impl(Time, Real, bool) method in derived classes.

    Volatility are assumed to be expressed on an annual basis.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 bdc: BusinessDayConvention = BusinessDayConvention.Following,
                 dc: DayCounter = None):
        super(BlackVolatilityTermStructure, self).__init__(reference_date,
                                                           settlement_days,
                                                           cal,
                                                           bdc,
                                                           dc)

    def black_variance_impl(self,
                            maturity: Real,
                            strike: Real):
        """
        Returns the variance for the given strike and date calculating it
        from the volatility.
        """
        vol = self.black_vol_impl(maturity, strike)
        return vol * vol * maturity


class BlackVarianceTermStructure(BlackVolTermStructure):
    """
    Black variance term structure
    This abstract class acts as an adapter to VolTermStructure allowing
    the programmer to implement only the
    black_variance_impl(Time, Real, bool) method in derived classes.

    Volatility are assumed to be expressed on an annual basis.
    """

    def __init__(self,
                 reference_date: datetime = None,
                 settlement_days: int = None,
                 cal: Calendar = None,
                 bdc: BusinessDayConvention = BusinessDayConvention.Following,
                 dc: DayCounter = None):
        super(BlackVarianceTermStructure, self).__init__(reference_date,
                                                         settlement_days,
                                                         cal,
                                                         bdc,
                                                         dc)

    def black_vol_impl(self,
                       t: Real,
                       strike: Real):
        """
        Returns the volatility for the given strike and date calculating it
        from the variance.
        """
        non_zero_maturity = 0.00001 if t == 0.0 else t
        var = self.black_variance_impl(non_zero_maturity, strike)
        return math.sqrt(var / non_zero_maturity)
