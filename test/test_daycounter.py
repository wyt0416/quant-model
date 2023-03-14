from datetime import datetime, timedelta
from typing import List
from loguru import logger

from qtmodel.error import TestError, qt_require, QTError, NotCatchError
from qtmodel.settings import Settings
from qtmodel.time.calendars.brazil import Brazil
from qtmodel.time.calendars.canada import Canada
from qtmodel.time.calendars.china import China
from qtmodel.time.date import DateTool
from qtmodel.time.daycounter import DayCounter
from qtmodel.time.daycounters import *
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendars.nullcalendar import NullCalendar
from qtmodel.time.dategenerationrule import DateGenerationTypes
from qtmodel.time.daycounters.actual365fixed import Actual365Fixed, Actual365FixedConventionTypes
from qtmodel.time.daycounters.actualactual import ActualActualConventionTypes, ActualActual
from qtmodel.time.daycounters.business252 import Business252
from qtmodel.time.daycounters.one import OneDayCounter
from qtmodel.time.daycounters.simpledaycounter import SimpleDayCounter
from qtmodel.time.daycounters.thirty360 import Thirty360, Thirty360ConventionTypes
from qtmodel.time.frequency import Frequency
from qtmodel.time.schedule import Schedule, MakeSchedule
from qtmodel.time.calendar import CalendarTypes
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.calendars.weekendsonly import WeekendsOnly
from qtmodel.time.calendars.japan import Japan
from qtmodel.time.calendars.unitedstates import UnitedStates
from qtmodel.time.calendars.target import TARGET


class SingleCase:
    def __init__(self,
                 convention: ActualActualConventionTypes = None,
                 start: datetime = None,
                 end: datetime = None,
                 ref_start: datetime = None,
                 ref_end: datetime = None,
                 result: float = None):
        self.convention = convention
        self.start = start
        self.end = end
        self.ref_start = ref_start
        self.ref_end = ref_end
        self.result = result


def isma_year_fraction_with_reference_dates(day_counter: DayCounter = None,
                                            start: datetime = None,
                                            end: datetime = None,
                                            ref_start: datetime = None,
                                            ref_end: datetime = None):
    reference_day_count = day_counter.day_count(ref_start, ref_end)
    # guess how many coupon periods per year:
    coupons_per_year = round(365.0 / reference_day_count)
    # the above is good enough for annual or semi-annual payments.
    return day_counter.day_count(start, end) / (reference_day_count * coupons_per_year)


def actual_actual_daycount_computation(schedule: Schedule = None,
                                       start: datetime = None,
                                       end: datetime = None):
    day_counter = ActualActual(convention=ActualActualConventionTypes.ISMA,
                               schedule=schedule)
    year_fraction = 0.0

    for i in range(1, schedule.size() - 1):
        reference_start = schedule.dates[i]
        reference_end = schedule.dates[i + 1]
        if start < reference_end and end > reference_start:
            year_fraction += isma_year_fraction_with_reference_dates(day_counter,
                                                                     start if start > reference_start else reference_start,
                                                                     end if end < reference_end else reference_end,
                                                                     reference_start,
                                                                     reference_end)

    return year_fraction


def test_actual_actual():
    print("Testing actual/actual day counters...")

    test_cases = []
    # first example
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=datetime(2003, 11, 1),
                                 end=datetime(2004, 5, 1),
                                 result=0.497724380567))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(2003, 11, 1)),
                                 end=(datetime(2004, 5, 1)),
                                 ref_start=(datetime(2003, 11, 1)),
                                 ref_end=(datetime(2004, 5, 1)),
                                 result=.500000000000))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=datetime(2003, 11, 1),
                                 end=datetime(2004, 5, 1),
                                 result=0.497267759563))
    # short first calculation period (first period)
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(1999, 2, 1)),
                                 end=(datetime(1999, 7, 1)),
                                 result=.410958904110))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(1999, 2, 1)),
                                 end=(datetime(1999, 7, 1)),
                                 ref_start=(datetime(1998, 7, 1)),
                                 ref_end=(datetime(1999, 7, 1)),
                                 result=0.410958904110))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(1999, 2, 1)),
                                 end=(datetime(1999, 7, 1)),
                                 result=0.410958904110))
    # short first calculation period (second period)
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(1999, 7, 1)),
                                 end=(datetime(2000, 7, 1)),
                                 result=1.001377348600))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(1999, 7, 1)),
                                 end=(datetime(2000, 7, 1)),
                                 ref_start=(datetime(1999, 7, 1)),
                                 ref_end=(datetime(2000, 7, 1)),
                                 result=1.000000000000))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(1999, 7, 1)),
                                 end=(datetime(2000, 7, 1)),
                                 result=.000000000000))
    # long first calculation period (first period)
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(2002, 8, 15)),
                                 end=(datetime(2003, 7, 15)),
                                 result=0.915068493151))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(2002, 8, 15)),
                                 end=(datetime(2003, 7, 15)),
                                 ref_start=(datetime(2003, 1, 15)),
                                 ref_end=(datetime(2003, 7, 15)),
                                 result=0.915760869565))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(2002, 8, 15)),
                                 end=(datetime(2003, 7, 15)),
                                 result=0.915068493151))
    # long first calculation period (second period)
    # Warning: the ISDA case is in disagreement with mktc1198.pdf
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(2003, 7, 15)),
                                 end=(datetime(2004, 1, 15)),
                                 result=0.504004790778))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(2003, 7, 15)),
                                 end=(datetime(2004, 1, 15)),
                                 ref_start=(datetime(2003, 7, 15)),
                                 ref_end=(datetime(2004, 1, 15)),
                                 result=0.500000000000))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(2003, 7, 15)),
                                 end=(datetime(2004, 1, 15)),
                                 result=0.504109589041))
    # short final calculation period (penultimate period)
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(1999, 7, 30)),
                                 end=(datetime(2000, 1, 30)),
                                 result=0.503892506924))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(1999, 7, 30)),
                                 end=(datetime(2000, 1, 30)),
                                 ref_start=(datetime(1999, 7, 30)),
                                 ref_end=(datetime(2000, 1, 30)),
                                 result=0.500000000000))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(1999, 7, 30)),
                                 end=(datetime(2000, 1, 30)),
                                 result=0.504109589041))
    # short final calculation period (final period)
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISDA,
                                 start=(datetime(2000, 1, 30)),
                                 end=(datetime(2000, 6, 30)),
                                 result=0.415300546448))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.ISMA,
                                 start=(datetime(2000, 1, 30)),
                                 end=(datetime(2000, 6, 30)),
                                 ref_start=(datetime(2000, 1, 30)),
                                 ref_end=(datetime(2000, 7, 30)),
                                 result=0.417582417582))
    test_cases.append(SingleCase(convention=ActualActualConventionTypes.AFB,
                                 start=(datetime(2000, 1, 30)),
                                 end=(datetime(2000, 6, 30)),
                                 result=0.41530054644))

    n = len(test_cases)
    for i in range(n):
        day_counter = ActualActual(test_cases[i].convention)
    d1 = test_cases[i].start
    d2 = test_cases[i].end
    rd1 = test_cases[i].ref_start
    rd2 = test_cases[i].ref_end
    calculated = day_counter.year_fraction(d1, d2, rd1, rd2)

    if abs(calculated - test_cases[i].result) > 1.0e-10:
        ref_period = str()
        period = "period: " + str(d1) + " to " + str(d2)
        if test_cases[i].convention == ActualActualConventionTypes.ISMA:
            ref_period = "referencePeriod: " + str(rd1) + " to " + str(rd2)
        raise QTError(
            f"{day_counter.name()}:\n {period}\n {ref_period} \n calculated: {round(calculated, 10)} \n "
            f"expected: {round(test_cases[i].result, 10)}")


def test_actual_actual_isma():
    is_end_of_month = False
    frequency = Frequency.Semiannual
    interest_accrual_date = datetime(1999, 1, 30)
    maturity_date = datetime(2000, 6, 30)
    first_coupon_date = datetime(1999, 7, 30)
    penultimate_coupon_date = datetime(2000, 1, 30)
    d1 = datetime(2000, 1, 30)
    d2 = datetime(2000, 6, 30)

    expected = (152. / (182. * 2))

    schedule = MakeSchedule().begin(interest_accrual_date).end(maturity_date).with_frequency(frequency).with_first_date(
        first_coupon_date).with_next_to_last_date(penultimate_coupon_date).end_of_month(is_end_of_month).schedule()

    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)
    calculated = day_counter.year_fraction(d1, d2)

    if abs(calculated - expected) > 1.0e-10:
        period = "period: " + str(d1) + " to " + str(d2) + "\n first_coupon_date: " + str(
            first_coupon_date) + "\n penultimate_coupon_date" \
                 + str(penultimate_coupon_date)
        raise QTError(
            f"{day_counter.name()}:\n {period} \n calculated: {round(calculated, 10)} \n expected: {round(expected, 10)}")

    ###############################################################################

    is_end_of_month = True
    frequency = Frequency.Quarterly
    interest_accrual_date = datetime(1999, 5, 31)
    maturity_date = datetime(2000, 4, 30)
    first_coupon_date = datetime(1999, 8, 31)
    penultimate_coupon_date = datetime(1999, 11, 30)
    d1 = datetime(1999, 11, 30)
    d2 = datetime(2000, 4, 30)

    expected = 91.0 / (91.0 * 4) + 61.0 / (92.0 * 4)

    schedule = MakeSchedule().begin(interest_accrual_date).end(maturity_date).with_frequency(frequency).with_first_date(
        first_coupon_date).with_next_to_last_date(penultimate_coupon_date).end_of_month(is_end_of_month).schedule()

    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)
    calculated = day_counter.year_fraction(d1, d2)

    if abs(calculated - expected) > 1.0e-10:
        period = "period: " + str(d1) + " to " + str(d2) + "\n first_coupon_date: " + str(
            first_coupon_date) + "\n penultimate_coupon_date"
        + str(penultimate_coupon_date)
        raise QTError(
            f"{day_counter.name()}:\n {period} \n calculated: {round(calculated, 10)} \n expected: {round(expected, 10)}")

    ###############################################################################

    is_end_of_month = False
    frequency = Frequency.Quarterly
    interest_accrual_date = datetime(1999, 5, 31)
    maturity_date = datetime(2000, 4, 30)
    first_coupon_date = datetime(1999, 8, 31)
    penultimate_coupon_date = datetime(1999, 11, 30)
    d1 = datetime(1999, 11, 30)
    d2 = datetime(2000, 4, 30)

    expected = 91.0 / (91.0 * 4) + 61.0 / (90.0 * 4)

    schedule = MakeSchedule().begin(interest_accrual_date).end(maturity_date).with_frequency(frequency).with_first_date(
        first_coupon_date).with_next_to_last_date(penultimate_coupon_date).end_of_month(is_end_of_month).schedule()

    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)
    calculated = day_counter.year_fraction(d1, d2)

    if abs(calculated - expected) > 1.0e-10:
        period = "period: " + str(d1) + " to " + str(d2) + "\n first_coupon_date: " + str(
            first_coupon_date) + "\n penultimate_coupon_date"
        + str(penultimate_coupon_date)
        raise QTError(
            f"{day_counter.name()}:\n {period} \n calculated: {round(calculated, 10)} \n expected: {round(expected, 10)}")


def test_actual_actual_with_semiannual_schedule():
    print("Testing actual/actual with schedule "
          "for undefined semiannual reference periods...")

    calendar = UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)
    from_date = datetime(2017, 1, 10)
    first_coupon = datetime(2017, 8, 31)
    quasi_coupon = datetime(2017, 2, 28)
    quasi_coupon2 = datetime(2016, 8, 31)

    schedule = MakeSchedule().begin(from_date).with_first_date(first_coupon).end(datetime(2026, 2, 28)).with_frequency(
        Frequency.Semiannual).with_calendar(calendar).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month(True).schedule()

    test_date = schedule.dates[1]
    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)
    day_counter_no_schedule = ActualActual(ActualActualConventionTypes.ISMA)

    reference_period_start = schedule.dates[1]
    reference_period_end = schedule.dates[2]

    # Test
    assert day_counter.year_fraction(reference_period_start, reference_period_start) == 0.0, "This should be zero."
    assert day_counter_no_schedule.year_fraction(reference_period_start,
                                                 reference_period_start) == 0.0, "This should be zero"
    assert day_counter_no_schedule.year_fraction(reference_period_start,
                                                 reference_period_start,
                                                 reference_period_start,
                                                 reference_period_start) == 0.0, "This should be zero"
    assert day_counter.year_fraction(reference_period_start,
                                     reference_period_end) == 0.5, f"This should be exact using schedule; " \
                                                                   f"{reference_period_start} to {reference_period_end}" \
                                                                   f" Should be 0.5 "
    assert day_counter_no_schedule.year_fraction(reference_period_start,
                                                 reference_period_end,
                                                 reference_period_start,
                                                 reference_period_end) == 0.5, "This should be exact for explicit " \
                                                                               "reference periods with no schedule"

    while test_date < reference_period_end:
        difference = day_counter.year_fraction(test_date, reference_period_end, reference_period_start,
                                               reference_period_end) - day_counter.year_fraction(test_date,
                                                                                                 reference_period_end)
        if abs(difference) > 1.0e-10:
            raise QTError("Failed to correctly use the schedule to find the reference period for Act/Act")
        test_date = calendar.advance(test_date, 1, TimeUnit.Days)

    # Test long first coupon
    calculated_year_fraction = day_counter.year_fraction(from_date, first_coupon)
    expected_year_fraction = 0.5 + day_counter.day_count(from_date, quasi_coupon) / (
            2 * day_counter.day_count(quasi_coupon2, quasi_coupon))
    assert abs(
        calculated_year_fraction - expected_year_fraction) < 1.0e-10, f"failed_to_compute_the_expected_year_fraction \n " \
                                                                      f"expected: {expected_year_fraction} \n calculated: {calculated_year_fraction}"

    # test multiple periods
    schedule = MakeSchedule().begin(datetime(2017, 1, 10)).with_first_date(datetime(2017, 8, 31)).end(
        datetime(2026, 2, 28)).with_frequency(Frequency.Semiannual).with_calendar(calendar).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month(False).schedule()

    period_start_date = schedule.dates[1]
    period_end_date = schedule.dates[2]

    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)
    while period_end_date < schedule.dates[schedule.size() - 2]:
        expected = actual_actual_daycount_computation(schedule,
                                                      period_start_date,
                                                      period_end_date)
        calculated = day_counter.year_fraction(period_start_date,
                                               period_end_date)
        if abs(expected - calculated) > 1e-8:
            raise QTError(
                f"Failed to compute the correct year fraction given a schedule: {period_start_date} to"
                f" {period_end_date} \n expected: {expected} \n calculated: {calculated}")
        period_end_date = calendar.advance(period_end_date, 1, TimeUnit.Days)


def test_actual_actual_with_annual_schedule():
    print("Testing actual/actual with schedule for undefined annual reference periods...")
    calendar = UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)
    schedule = MakeSchedule().begin(datetime(2017, 1, 10)).with_first_date(datetime(2017, 8, 31)).end(
        datetime(2026, 2, 28)).with_frequency(Frequency.Annual).with_calendar(calendar).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month(False).schedule()

    reference_period_start = schedule.dates[1]
    reference_period_end = schedule.dates[2]

    test_date = schedule.dates[1]
    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)

    while test_date < reference_period_end:
        difference = isma_year_fraction_with_reference_dates(day_counter, test_date, reference_period_end,
                                                             reference_period_start,
                                                             reference_period_end) - day_counter.year_fraction(
            test_date, reference_period_end)
        if abs(difference) > 1.0e-10:
            raise QTError(f"Failed to correctly use the schedule to find the reference period for Act/Act \n"
                          f"{test_date} to {reference_period_end} \n Ref: {reference_period_start} to {reference_period_end}")
        test_date = calendar.advance(test_date, 1, TimeUnit.Days)


def test_actual_actual_with_schedule():
    print("Testing actual/actual day counter with schedule...")
    # long first coupon
    issue_date_expected = datetime(2017, 1, 17)
    first_coupon_date_expected = datetime(2017, 8, 31)

    schedule = MakeSchedule().begin(issue_date_expected).with_first_date(first_coupon_date_expected).end(
        datetime(2026, 2, 28)).with_frequency(Frequency.Semiannual).with_calendar(Canada()).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month().schedule()

    issue_date = schedule.dates[0]
    qt_require(issue_date == issue_date_expected,
               f"This is not the expected issue date {issue_date} expected {issue_date_expected}")
    first_coupon_date = schedule.dates[1]
    qt_require(first_coupon_date == first_coupon_date_expected,
               f"This is not the expected coupon date  {first_coupon_date} expected {first_coupon_date_expected}")

    # Make thw quasi coupon dates:
    quasi_coupon_date2 = schedule.calendar.advance(date=first_coupon_date,
                                                   period=-schedule.tenor(),
                                                   convention=schedule.convention,
                                                   end_of_month=schedule.end_of_month())
    quasi_coupon_date1 = schedule.calendar.advance(date=quasi_coupon_date2,
                                                   period=-schedule.tenor(),
                                                   convention=schedule.convention,
                                                   end_of_month=schedule.end_of_month())

    quasi_coupon_date1_expected = datetime(2016, 8, 31)
    quasi_coupon_date2_expected = datetime(2017, 2, 28)
    qt_require(quasi_coupon_date2 == quasi_coupon_date2_expected,
               f"Expected {quasi_coupon_date2_expected} as the later quasi coupon date but received {quasi_coupon_date2}")
    qt_require(quasi_coupon_date1 == quasi_coupon_date1_expected,
               f"Expected {quasi_coupon_date1_expected} as the later quasi coupon date but received {quasi_coupon_date1}")

    day_counter = ActualActual(ActualActualConventionTypes.ISMA, schedule)

    # full coupon
    t_with_reference = day_counter.year_fraction(issue_date, first_coupon_date, quasi_coupon_date2, first_coupon_date)
    t_no_reference = day_counter.year_fraction(issue_date, first_coupon_date)
    t_total = isma_year_fraction_with_reference_dates(day_counter, issue_date, quasi_coupon_date2, quasi_coupon_date1,
                                                      quasi_coupon_date2) + 0.5
    expected = 0.6160220994
    if abs(t_total - expected) > 1.0e-10:
        raise QTError(f"Failed to reproduce expected time:\n"
                      f"calculated: {round(t_total, 10)}\nexpected: {round(expected), 10}")

    if abs(t_with_reference - expected) > 1.0e-10:
        raise QTError(f"Failed to reproduce expected time:\n"
                      f"calculated: {round(t_with_reference, 10)}\nexpected: {round(expected), 10}")

    if abs(t_no_reference - t_with_reference) > 1.0e-10:
        raise QTError("Should produce the same time whether or not references are present")

    # settlement date in the first quasi-period
    settlement_date = datetime(2017, 1, 29)
    t_with_reference = isma_year_fraction_with_reference_dates(day_counter, issue_date, settlement_date,
                                                               quasi_coupon_date1, quasi_coupon_date2)
    t_no_reference = day_counter.year_fraction(issue_date, settlement_date)
    t_expected_first_qp = 0.03314917127071823
    if abs(t_with_reference - t_expected_first_qp) > 1.0e-10:
        raise QTError(f"Failed to reproduce expected time:\n"
                      f"calculated: {round(t_with_reference, 10)}\nexpected: {round(t_expected_first_qp), 10}")

    if abs(t_no_reference - t_with_reference) > 1.0e-10:
        raise QTError("Should produce the same time whether or not references are present")

    t2 = day_counter.year_fraction(settlement_date, first_coupon_date)
    if abs(t_expected_first_qp + t2 - expected) > 1.0e-10:
        raise QTError("Sum of quasiperiod2 split is not consistent")

    # settlement date in the second quasi-period
    settlement_date = datetime(2017, 7, 29)
    t_no_reference = day_counter.year_fraction(issue_date, settlement_date)
    t_with_reference = isma_year_fraction_with_reference_dates(
        day_counter, issue_date, quasi_coupon_date2, quasi_coupon_date1,
        quasi_coupon_date2) + isma_year_fraction_with_reference_dates(
        day_counter, quasi_coupon_date2, settlement_date, quasi_coupon_date2, first_coupon_date)

    if abs(t_no_reference - t_with_reference) > 1.0e-10:
        raise QTError("These two cases should be identical")

    t2 = day_counter.year_fraction(settlement_date, first_coupon_date)
    if abs(t_total - t2 - t_no_reference) > 1.0e-10:
        raise QTError(f"Failed to reproduce expected time:\n"
                      f"calculated: {round(t_total, 10)}\nexpected: {round(t2 + t_no_reference), 10}")


def test_simple():
    print("Testing simple day counter...")
    p = [Period(3, TimeUnit.Months), Period(6, TimeUnit.Months), Period(1, TimeUnit.Years)]
    expected = [0.25, 0.5, 1.0]
    n = len(p)

    # 4 years should be enough
    first = datetime(2002, 1, 1)
    last = datetime(2005, 12, 31)
    day_counter = SimpleDayCounter()
    one_day = timedelta(days=1)

    start = first
    while start <= last:
        for i in range(n):
            end = DateTool.advance(date=start, period=p[i])
            calculated = day_counter.year_fraction(start, end)
            if abs(calculated - expected[i]) > 1.0e-12:
                raise QTError(
                    f"from {start} to {end} \n calculated: {round(calculated, 12)}\n expected: {round(expected[i], 12)}")
        start += one_day


def test_one():
    print("Testing 1/1 day counter...")
    p = [Period(3, TimeUnit.Months), Period(6, TimeUnit.Months), Period(1, TimeUnit.Years)]
    expected = [01.0, 1.0, 1.0]
    n = len(p)

    # 1 years should be enough
    first = datetime(2002, 1, 1)
    last = datetime(2005, 12, 31)
    day_counter = OneDayCounter()
    one_day = timedelta(days=1)

    start = first
    while start <= last:
        for i in range(n):
            end = DateTool.advance(date=start, period=p[i])
            calculated = day_counter.year_fraction(start, end)
            if abs(calculated - expected[i]) > 1.0e-12:
                raise QTError(
                    f"from {start} to {end} \n calculated: {round(calculated, 12)}\n expected: {round(expected[i], 12)}")
        start += one_day


def test_business_252():
    print("Testing business/252 day counter...")
    test_dates = [datetime(2002, 2, 1)]
    test_dates.append(datetime(2002, 2, 4))
    test_dates.append(datetime(2003, 5, 16))
    test_dates.append(datetime(2003, 12, 17))
    test_dates.append(datetime(2004, 12, 17))
    test_dates.append(datetime(2005, 12, 19))
    test_dates.append(datetime(2006, 1, 2))
    test_dates.append(datetime(2006, 3, 13))
    test_dates.append(datetime(2006, 5, 15))
    test_dates.append(datetime(2006, 3, 17))
    test_dates.append(datetime(2006, 5, 15))
    test_dates.append(datetime(2006, 7, 26))
    test_dates.append(datetime(2007, 6, 28))
    test_dates.append(datetime(2009, 9, 16))
    test_dates.append(datetime(2016, 7, 26))

    expected = [0.0039682539683,
                1.2738095238095,
                0.6031746031746,
                0.9960317460317,
                1.0000000000000,
                0.0396825396825,
                0.1904761904762,
                0.1666666666667,
                -0.1507936507937,
                0.1507936507937,
                0.2023809523810,
                0.912698412698,
                2.214285714286,
                6.84126984127]

    day_counter1 = Business252(Brazil())

    for i in range(1, len(test_dates)):
        calculated = day_counter1.year_fraction(test_dates[i - 1], test_dates[i])
        if abs(calculated - expected[i - 1]) > 1.0e-12:
            raise QTError(
                f"from {test_dates[i - 1]} to {test_dates[i]} \n calculated: {round(calculated, 12)}\n"
                f" expected: {round(expected[i], 12)}")

    day_counter2 = Business252()
    for i in range(1, len(test_dates)):
        calculated = day_counter2.year_fraction(test_dates[i - 1], test_dates[i])
        if abs(calculated - expected[i - 1]) > 1.0e-12:
            raise QTError(
                f"from {test_dates[i - 1]} to {test_dates[i]} \n calculated: {round(calculated, 12)}\n"
                f" expected: {round(expected[i], 12)}")


def test_thirty_360_bond_basis():
    print("Testing 30/360 day counter (Bond Basis)...")
    # See https://www.isda.org/2008/12/22/30-360-day-count-conventions/

    day_counter = Thirty360(Thirty360ConventionTypes.EurobondBasis)
    data = []
    # Example 1: End dates do not involve the last day of February
    data.append([datetime(2006, 8, 20), datetime(2007, 2, 20), 180])
    data.append([datetime(2007, 2, 20), datetime(2007, 8, 20), 180])
    data.append([datetime(2007, 8, 20), datetime(2008, 2, 20), 180])
    data.append([datetime(2008, 2, 20), datetime(2008, 8, 20), 180])
    data.append([datetime(2008, 8, 20), datetime(2009, 2, 20), 180])
    data.append([datetime(2009, 2, 20), datetime(2009, 8, 20), 180])

    # Example 2: End dates include some end-February dates
    data.append([datetime(2006, 2, 28), datetime(2006, 8, 31), 182])
    data.append([datetime(2006, 8, 31), datetime(2007, 2, 28), 178])
    data.append([datetime(2007, 2, 28), datetime(2007, 8, 31), 182])
    data.append([datetime(2007, 8, 31), datetime(2008, 2, 29), 179])
    data.append([datetime(2008, 2, 29), datetime(2008, 8, 31), 181])
    data.append([datetime(2008, 8, 31), datetime(2009, 2, 28), 178])
    data.append([datetime(2009, 2, 28), datetime(2009, 8, 31), 182])
    data.append([datetime(2009, 8, 31), datetime(2010, 2, 28), 178])
    data.append([datetime(2010, 2, 28), datetime(2010, 8, 31), 182])
    data.append([datetime(2010, 8, 31), datetime(2011, 2, 28), 178])
    data.append([datetime(2011, 2, 28), datetime(2011, 8, 31), 182])
    data.append([datetime(2011, 8, 31), datetime(2012, 2, 29), 179])

    # Example 3: Miscellaneous calculations
    data.append([datetime(2006, 1, 31), datetime(2006, 2, 28), 28])
    data.append([datetime(2006, 1, 30), datetime(2006, 2, 28), 28])
    data.append([datetime(2006, 2, 28), datetime(2006, 3, 3), 5])
    data.append([datetime(2006, 2, 14), datetime(2006, 2, 28), 14])
    data.append([datetime(2006, 9, 30), datetime(2006, 10, 31), 30])
    data.append([datetime(2006, 10, 31), datetime(2006, 11, 28), 28])
    data.append([datetime(2007, 8, 31), datetime(2008, 2, 28), 178])
    data.append([datetime(2008, 2, 28), datetime(2008, 8, 28), 180])
    data.append([datetime(2008, 2, 28), datetime(2008, 8, 30), 182])
    data.append([datetime(2008, 2, 28), datetime(2008, 8, 31), 182])
    data.append([datetime(2007, 2, 26), datetime(2008, 2, 28), 362])
    data.append([datetime(2007, 2, 26), datetime(2008, 2, 29), 363])
    data.append([datetime(2008, 2, 29), datetime(2009, 2, 28), 359])
    data.append([datetime(2008, 2, 28), datetime(2008, 3, 30), 32])
    data.append([datetime(2008, 2, 28), datetime(2008, 3, 31), 32])

    for x in data:
        calculated = day_counter.day_count(x[0], x[1])
        if calculated != x[2]:
            raise QTError(f"from {x[0]} to {x[1]} \ncalculated: {calculated}\nexpected: {x[2]}")


def test_thirty_360_isda():
    print("Testing 30/360 day counter (ISDA)...")
    # See https://www.isda.org/2008/12/22/30-360-day-count-conventions/
    data1 = []
    data1.append([datetime(2006, 8, 20), datetime(2007, 2, 20), 180])
    data1.append([datetime(2007, 2, 20), datetime(2007, 8, 20), 180])
    data1.append([datetime(2007, 8, 20), datetime(2008, 2, 20), 180])
    data1.append([datetime(2008, 2, 20), datetime(2008, 8, 20), 180])
    data1.append([datetime(2008, 8, 20), datetime(2009, 2, 20), 180])
    data1.append([datetime(2009, 2, 20), datetime(2009, 8, 20), 180])

    termination_date = datetime(2009, 8, 20)
    day_counter = Thirty360(Thirty360ConventionTypes.ISDA, termination_date)

    for x in data1:
        calculated = day_counter.day_count(x[0], x[1])
        if calculated != x[2]:
            raise QTError(f"from {x[0]} to {x[1]} \ncalculated: {calculated}\nexpected: {x[2]}")

    data2 = []
    data2.append([datetime(2006, 2, 28), datetime(2006, 8, 31), 180])
    data2.append([datetime(2006, 8, 31), datetime(2007, 2, 28), 180])
    data2.append([datetime(2007, 2, 28), datetime(2007, 8, 31), 180])
    data2.append([datetime(2007, 8, 31), datetime(2008, 2, 29), 180])
    data2.append([datetime(2008, 2, 29), datetime(2008, 8, 31), 180])
    data2.append([datetime(2008, 8, 31), datetime(2009, 2, 28), 180])
    data2.append([datetime(2009, 2, 28), datetime(2009, 8, 31), 180])
    data2.append([datetime(2009, 8, 31), datetime(2010, 2, 28), 180])
    data2.append([datetime(2010, 2, 28), datetime(2010, 8, 31), 180])
    data2.append([datetime(2010, 8, 31), datetime(2011, 2, 28), 180])
    data2.append([datetime(2011, 2, 28), datetime(2011, 8, 31), 180])
    data2.append([datetime(2011, 8, 31), datetime(2012, 2, 29), 179])

    termination_date = datetime(2012, 2, 29)
    day_counter = Thirty360(Thirty360ConventionTypes.ISDA, termination_date)

    for x in data2:
        calculated = day_counter.day_count(x[0], x[1])
        if calculated != x[2]:
            raise QTError(f"from {x[0]} to {x[1]} \ncalculated: {calculated}\nexpected: {x[2]}")

    data3 = []
    data3.append([datetime(2006, 1, 31), datetime(2006, 2, 28), 30])
    data3.append([datetime(2006, 1, 30), datetime(2006, 2, 28), 30])
    data3.append([datetime(2006, 2, 28), datetime(2006, 3, 3), 3])
    data3.append([datetime(2006, 2, 14), datetime(2006, 2, 28), 16])
    data3.append([datetime(2006, 9, 30), datetime(2006, 10, 31), 30])
    data3.append([datetime(2006, 10, 31), datetime(2006, 11, 28), 28])
    data3.append([datetime(2007, 8, 31), datetime(2008, 2, 28), 178])
    data3.append([datetime(2008, 2, 28), datetime(2008, 8, 28), 180])
    data3.append([datetime(2008, 2, 28), datetime(2008, 8, 30), 182])
    data3.append([datetime(2008, 2, 28), datetime(2008, 8, 31), 182])
    data3.append([datetime(2007, 2, 28), datetime(2008, 2, 28), 358])
    data3.append([datetime(2007, 2, 28), datetime(2008, 2, 29), 359])
    data3.append([datetime(2008, 2, 29), datetime(2009, 2, 28), 360])
    data3.append([datetime(2008, 2, 29), datetime(2008, 3, 30), 30])
    data3.append([datetime(2008, 2, 29), datetime(2008, 3, 31), 30])

    termination_date = datetime(2008, 2, 29)
    day_counter = Thirty360(Thirty360ConventionTypes.ISDA, termination_date)

    for x in data3:
        calculated = day_counter.day_count(x[0], x[1])
        if calculated != x[2]:
            raise QTError(f"from {x[0]} to {x[1]} \ncalculated: {calculated}\nexpected: {x[2]}")


def test_actual_365_canadian():
    print("Testing that Actual/365 (Canadian) throws when needed...")

    day_counter = Actual365Fixed(Actual365FixedConventionTypes.Canadian)

    try:
        #  no reference period
        day_counter.year_fraction(datetime(2018, 9, 10), datetime(2019, 9, 10))
        raise NotCatchError("Invalid call to yearFraction failed to throw")
    except QTError:
        pass  # expected

    try:
        #  reference period shorter than a month
        day_counter.year_fraction(datetime(2018, 9, 10),
                                  datetime(2018, 9, 12),
                                  datetime(2018, 9, 10),
                                  datetime(2018, 9, 15)
                                  )
        raise NotCatchError("Invalid call to yearFraction failed to throw")
    except QTError:
        pass  # expected


def test_actual_actual_out_of_schedule_range():
    today = datetime(2020, 11, 10)
    temp = Settings().evaluation_date
    Settings().evaluation_date = today

    effective_date = datetime(2019, 5, 21)
    termination_date = datetime(2029, 5, 21)
    tenor = Period(1, TimeUnit.Years)
    calendar = China(CalendarTypes.CHINA_IB)
    convention = BusinessDayConvention.Unadjusted
    termination_date_convention = convention
    gen_rule = DateGenerationTypes.Backward
    end_of_month = False

    schedule = MakeSchedule().begin(effective_date).end(termination_date).with_tenor(tenor).with_calendar(
        calendar).with_convention(convention).with_termination_date_convention(termination_date_convention).with_rule(
        gen_rule).end_of_month(end_of_month).schedule()
    day_counter = ActualActual(ActualActualConventionTypes.Bond, schedule)
    raised = False
    try:
        day_counter.year_fraction(today, DateTool.advance(date=today, period=Period(9, TimeUnit.Years)))
    except:
        raised = True
    if not raised:
        raise QTError("Exception expected but did not happen!")
