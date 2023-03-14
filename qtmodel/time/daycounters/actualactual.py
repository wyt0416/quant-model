import calendar
import copy
from datetime import datetime, timedelta
from enum import Enum

from qtmodel.error import qt_require, QTError
from qtmodel.time.date import DateTool
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.schedule import Schedule
from qtmodel.time.timeunit import TimeUnit


class ActualActualConventionTypes(Enum):
    """ Actual/Actual day count
        The day count can be calculated according to:

        - the ISDA convention, also known as "Actual/Actual (Historical)",
          "Actual/Actual", "Act/Act", and according to ISDA also "Actual/365",
          "Act/365", and "A/365";
        - the ISMA and US Treasury convention, also known as
          "Actual/Actual (Bond)";
        - the AFB convention, also known as "Actual/Actual (Euro)".

        For more details, refer to
        https://www.isda.org/a/pIJEE/The-Actual-Actual-Day-Count-Fraction-1999.pdf """
    ISMA = "Actual/Actual (ISMA)"
    Bond = "Actual/Actual (Bond)"
    ISDA = "Actual/Actual (ISDA)"
    Historical = "Actual/Actual (Historical)"
    Actual365 = "Actual/365"
    AFB = "Actual/Actual (AFB)"
    Euro = "Actual/Actual (Euro)"


class ActualActual(DayCounter):

    def __init__(self,
                 convention: ActualActualConventionTypes = ActualActualConventionTypes.ISDA,
                 schedule: Schedule = None):
        self.convention = convention
        self.schedule = schedule

    def name(self):
        return self.convention.value

    def year_fraction(self,
                      date1: datetime,
                      date2: datetime,
                      ref_period_start: datetime = None,
                      ref_period_end: datetime = None):
        convention = self.convention
        if convention == ActualActualConventionTypes.ISMA or convention == ActualActualConventionTypes.Bond:
            if self.schedule is not None and not self.schedule.empty():
                return self.year_fraction_isma(date1, date2, ref_period_start, ref_period_end)
            else:
                return self.year_fraction_old_isma(date1, date2, ref_period_start, ref_period_end)
        elif convention == ActualActualConventionTypes.ISDA or \
                convention == ActualActualConventionTypes.Historical or \
                convention == ActualActualConventionTypes.Actual365:
            return self.year_fraction_isda(date1, date2)
        elif convention == ActualActualConventionTypes.AFB or \
                convention == ActualActualConventionTypes.Euro:
            return self.year_fraction_afb(date1, date2)
        else:
            raise QTError("unknown act/act convention")

    def year_fraction_isma(self,
                           date1: datetime,
                           date2: datetime,
                           ref_period_start: datetime = None,
                           ref_period_end: datetime = None):
        if date1 == date2:
            return 0.0
        elif date2 < date1:
            return -self.year_fraction(date2, date1, ref_period_start, ref_period_end)
        coupon_dates = self.get_list_of_period_dates_including_quasi_payments(self.schedule)

        first_date = min(coupon_dates)
        last_date = max(coupon_dates)

        qt_require(date1 >= first_date and date2 <= last_date,
                   f"Dates out of range of schedule: date 1: {date1}, date 2: {date2}, first date: {first_date}, last date: {last_date}")

        year_fraction_sum = 0.0
        i = 0
        while i < len(coupon_dates) - 1:
            start_reference_period = coupon_dates[i]
            end_reference_period = coupon_dates[i + 1]
            if date1 < end_reference_period and date2 > start_reference_period:
                year_fraction_sum += self.year_fraction_with_reference_dates(
                    max(date1, start_reference_period),
                    min(date2, end_reference_period),
                    start_reference_period,
                    end_reference_period)
            i += 1
        return year_fraction_sum

    def year_fraction_old_isma(self,
                               date1: datetime,
                               date2: datetime,
                               ref_period_start: datetime = None,
                               ref_period_end: datetime = None):
        if date1 == date2:
            return 0.0

        if date1 > date2:
            return -self.year_fraction(date2, date1, ref_period_start, ref_period_end)

        # when the reference period is not specified, try taking
        # it equal to (date1,date2)
        ref_period_start = ref_period_start if ref_period_start is not None else date1
        ref_period_end = ref_period_end if ref_period_end is not None else date2

        qt_require(ref_period_end > ref_period_start and ref_period_end > date1,
                   f'''invalid reference period: 
                   date 1: {date1}, 
                   date 2: {date2}, 
                   reference period start: {ref_period_start}, 
                   reference period end: {ref_period_end}''')

        # estimate roughly the length in months of a period
        months = round(12 * (ref_period_end - ref_period_start).days / 365)

        # for short periods...
        if months == 0:
            # ...take the reference period as 1 year from date1
            ref_period_start = date1
            ref_period_end = DateTool.advance(date=date1, n=1, units=TimeUnit.Years)
            months = 12

        period = months / 12.0

        if date2 <= ref_period_end:
            # here ref_period_end is a future (notional?) payment date
            if date1 >= ref_period_start:
                # here ref_period_start is the last (maybe notional)
                # payment date.
                # ref_period_start <= date1 <= date2 <= ref_period_end
                # [maybe the equality should be enforced, since
                # ref_period_start < date1 <= date2 < ref_period_end
                # could give wrong results] ???
                return period * DateTool.days_between(date1, date2) / DateTool.days_between(ref_period_start,
                                                                                            ref_period_end)
            else:
                # here ref_period_start is the next (maybe notional)
                # payment date and ref_period_end is the second next
                # (maybe notional) payment date.
                # date1 < ref_period_start < ref_period_end
                # AND date2 <= ref_period_end
                # this case is long first coupon

                # the last notional payment date
                previous_ref = DateTool.advance(date=ref_period_start, n=-months, units=TimeUnit.Months)

                if date2 > ref_period_start:
                    return self.year_fraction(date1,
                                              ref_period_start,
                                              previous_ref,
                                              ref_period_start) + self.year_fraction(ref_period_start,
                                                                                     date2,
                                                                                     ref_period_start,
                                                                                     ref_period_end)
                else:
                    return self.year_fraction(date1, date2, previous_ref, ref_period_start)

        else:
            # here ref_period_end is the last (notional?) payment date
            # date1 < ref_period_end < date2 AND ref_period_start < ref_period_end
            qt_require(ref_period_start <= date1,
                       "invalid dates: date1 < ref_period_start < ref_period_end < date2")
            # now it is: ref_period_start <= date1 < ref_period_end < date2

            # the part from date1 to ref_period_end
            sum_ = self.year_fraction(date1,
                                     ref_period_end,
                                     ref_period_start,
                                     ref_period_end)

            # the part from ref_period_end to date2
            # count how many regular periods are in [ref_period_end, date2],
            # then add the remaining time
            i = 0
            while 1:
                new_ref_start = DateTool.advance(date=ref_period_end, n=months * i, units=TimeUnit.Months)
                new_ref_end = DateTool.advance(date=ref_period_end, n=months * (i + 1), units=TimeUnit.Months)
                if date2 < new_ref_end:
                    break
                else:
                    sum_ += period
                    i += 1
            sum_ += self.year_fraction(new_ref_start, date2, new_ref_start, new_ref_end)
            return sum_

    def year_fraction_isda(self,
                           date1: datetime,
                           date2: datetime):
        if date1 == date2:
            return 0.0

        if date1 > date2:
            return -self.year_fraction(date2, date1, None, None)

        year1 = date1.year
        year2 = date2.year
        total_days_in_year1 = 366 if calendar.isleap(year1) else 365
        total_days_in_year2 = 366 if calendar.isleap(year2) else 365
        sum_ = year2 - year1 - 1
        # FLOATING_POINT_EXCEPTION
        sum_ += DateTool.days_between(date1, datetime(year1+1, 1, 1)) / total_days_in_year1
        sum_ += DateTool.days_between(datetime(year2, 1, 1), date2) / total_days_in_year2
        return sum_

    def year_fraction_afb(self,
                          date1: datetime,
                          date2: datetime):
        if date1 == date2:
            return 0.0

        if date1 > date2:
            return -self.year_fraction(date2, date1, None, None)

        new_date2 = date2
        temp = date2
        sum_ = 0.0
        while temp > date1:
            temp = DateTool.advance(date=new_date2, n=-1, units=TimeUnit.Years)
            if temp.day == 28 and temp.month == 2 and calendar.isleap(temp.year):
                temp += timedelta(days=1)
            if temp >= date1:
                sum_ += 1.0
                new_date2 = temp

        den = 365.0

        if calendar.isleap(new_date2.year):
            temp = datetime(new_date2.year, 2, 29)
            if new_date2 > temp >= date1:
                den += 1.0
        elif calendar.isleap(date1.year):
            temp = datetime(date1.year, 2, 29)
            if new_date2 > temp >= date1:
                den += 1.0

        return sum_ + DateTool.days_between(date1, new_date2) / den

    def find_coupons_per_year(self,
                              ref_start: datetime,
                              ref_end: datetime):
        # This will only work for day counts longer than 15 days.
        months = round(12 * self.day_count(date1=ref_start, date2=ref_end) / 365.0)
        return round(12.0 / months)

    def year_fraction_guess(self,
                            start: datetime,
                            end: datetime):
        # asymptotically correct.
        return self.day_count(date1=start, date2=end) / 365.0

    @staticmethod
    def get_list_of_period_dates_including_quasi_payments(schedule: Schedule):
        # Process the schedule into an array of dates.
        issue_date = schedule[0]
        new_dates = copy.deepcopy(schedule.dates)
        if not schedule.has_is_regular() or not schedule.is_regular(i=1):
            first_coupon = schedule[1]
            notional_first_coupon = schedule.calendar.advance(date=first_coupon,
                                                              period=-schedule.tenor(),
                                                              convention=schedule.convention,
                                                              end_of_month=schedule.end_of_month())
            new_dates[0] = notional_first_coupon

            # long first coupon
            if notional_first_coupon > issue_date:
                prior_notional_coupon = schedule.calendar.advance(date=notional_first_coupon,
                                                                  period=-schedule.tenor(),
                                                                  convention=schedule.convention,
                                                                  end_of_month=schedule.end_of_month())
                new_dates.insert(0, prior_notional_coupon)

        if not schedule.has_is_regular() or not schedule.is_regular(i=schedule.size() - 1):
            notional_last_coupon = schedule.calendar.advance(date=schedule[schedule.size() - 2],
                                                             period=schedule.tenor(),
                                                             convention=schedule.convention,
                                                             end_of_month=schedule.end_of_month())
            new_dates[schedule.size() - 1] = notional_last_coupon

            if notional_last_coupon < schedule.end_date():
                next_notional_coupon = schedule.calendar.advance(date=notional_last_coupon,
                                                                 period=schedule.tenor(),
                                                                 convention=schedule.convention,
                                                                 end_of_month=schedule.end_of_month())
                new_dates.append(next_notional_coupon)

        return new_dates

    def year_fraction_with_reference_dates(self,
                                           date1: datetime,
                                           date2: datetime,
                                           date3: datetime,
                                           date4: datetime):
        qt_require(date1 <= date2, f"This function is only correct if date1 <= date2\ndate1: {date1} date2: {date2}")

        reference_day_count = self.day_count(date1=date3, date2=date4)
        # guess how many coupon periods per year:
        if reference_day_count < 16:
            coupons_per_year = 1
            reference_day_count = self.day_count(date1=date1,
                                                 date2=DateTool.advance(date=date1, n=1, units=TimeUnit.Years))
        else:
            coupons_per_year = self.find_coupons_per_year(ref_start=date3, ref_end=date4)
        return self.day_count(date1=date1, date2=date2) / (reference_day_count * coupons_per_year)
