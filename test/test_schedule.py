from datetime import datetime, timedelta
from typing import List
from loguru import logger

from qtmodel.error import TestError, qt_require, QTError
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendars.nullcalendar import NullCalendar
from qtmodel.time.dategenerationrule import DateGenerationTypes
from qtmodel.time.frequency import Frequency
from qtmodel.time.schedule import Schedule, MakeSchedule
from qtmodel.time.calendar import CalendarTypes
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.calendars.weekendsonly import WeekendsOnly
from qtmodel.time.calendars.japan import Japan
from qtmodel.time.calendars.unitedstates import UnitedStates
from qtmodel.time.calendars.target import TARGET


def check_dates(schedule: Schedule = None,
                expected: List[datetime] = None):
    if schedule.size() != len(expected):
        raise TestError(f"expected {len(expected)} dates, found {schedule.size()}")
    for i in range(len(expected)):
        if schedule[i] != expected[i]:
            raise TestError(f"expected {expected[i]} at index {i}, found {schedule[i]}")


def make_cds_schedule(begin: datetime = None,
                      end: datetime = None,
                      rule: DateGenerationTypes = None):
    return MakeSchedule().begin(begin).end(end).with_calendar(WeekendsOnly).with_tenor(3,
                                                                                       TimeUnit.Months).with_convention(
        BusinessDayConvention.Following).with_termination_date_convention(BusinessDayConvention.Unadjusted).with_rule(
        rule)


def test_daily_schedule():
    print("Testing schedule with daily frequency...")

    start_date = datetime(2012, 1, 17)
    schedule = MakeSchedule().begin(start_date).end(start_date + timedelta(days=7)).with_calendar(
        TARGET()).with_frequency(Frequency.Daily).with_convention(BusinessDayConvention.Preceding).schedule()

    expected = [datetime(2012, 1, 17)]
    expected.append(datetime(2012, 1, 18))
    expected.append(datetime(2012, 1, 19))
    expected.append(datetime(2012, 1, 20))
    expected.append(datetime(2012, 1, 23))
    expected.append(datetime(2012, 1, 24))

    check_dates(schedule, expected)


def test_end_date_with_eom_adjustment():
    print("Testing end date for schedule with end-of-month adjustment...")

    schedule = MakeSchedule().begin(datetime(2009, 9, 30)).end(datetime(2012, 6, 15)).with_calendar(
        Japan()).with_tenor(Period(6, TimeUnit.Months)).with_convention(
        BusinessDayConvention.Following).with_termination_date_convention(
        BusinessDayConvention.Following).forwards().end_of_month().schedule()

    #  The end date is adjusted, so it should also be moved to the end of the month.
    expected = [datetime(2009, 9, 30)]
    expected.append(datetime(2010, 3, 31))
    expected.append(datetime(2010, 9, 30))
    expected.append(datetime(2011, 3, 31))
    expected.append(datetime(2011, 9, 30))
    expected.append(datetime(2012, 3, 30))
    expected.append(datetime(2012, 6, 29))

    check_dates(schedule, expected)


def test_dates_past_end_date_with_eom_adjustment():
    print("Testing that no dates are past the end date with EOM adjustment...")

    schedule = MakeSchedule().begin(datetime(2013, 3, 28)).end(datetime(2015, 3, 30)).with_calendar(
        TARGET()).with_tenor(Period(1, TimeUnit.Years)).with_convention(
        BusinessDayConvention.Unadjusted).with_termination_date_convention(
        BusinessDayConvention.Unadjusted).forwards().end_of_month().schedule()

    expected = [datetime(2013, 3, 31)]
    expected.append(datetime(2014, 3, 31))
    # March 31st 2015, coming from the EOM adjustment of March 28th,
    # should be discarded as past the end date.
    expected.append(datetime(2015, 3, 30))

    check_dates(schedule, expected)
    # also, the last period should not be regular.
    if schedule.is_regular(2):
        raise TestError(f"last period should not be regular")


def test_dates_same_as_end_date_with_eom_adjustment():
    print("Testing that next-to-last date same as end date is removed...")

    schedule = MakeSchedule().begin(datetime(2013, 3, 28)).end(datetime(2015, 3, 31)).with_calendar(
        TARGET()).with_tenor(Period(1, TimeUnit.Years)).with_convention(
        BusinessDayConvention.Unadjusted).with_termination_date_convention(
        BusinessDayConvention.Unadjusted).forwards().end_of_month().schedule()

    expected = [datetime(2013, 3, 31)]
    expected.append(datetime(2014, 3, 31))
    # March 31st 2015, coming from the EOM adjustment of March 28th,
    # should be discarded as past the end date.
    expected.append(datetime(2015, 3, 31))

    check_dates(schedule, expected)
    # also, the last period should not be regular.
    if not schedule.is_regular(2):
        raise TestError(f"last period should not be regular")


def test_forward_dates_with_eom_adjustment():
    print("Testing that the last date is not adjusted for EOM when termination date convention is unadjusted...")

    schedule = MakeSchedule().begin(datetime(1996, 8, 31)).end(datetime(1997, 9, 15)).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_tenor(
        Period(6, TimeUnit.Months)).with_convention(
        BusinessDayConvention.Unadjusted).with_termination_date_convention(
        BusinessDayConvention.Unadjusted).forwards().end_of_month().schedule()

    expected = [datetime(1996, 8, 31)]
    expected.append(datetime(1997, 2, 28))
    expected.append(datetime(1997, 8, 31))
    expected.append(datetime(1997, 9, 15))

    check_dates(schedule, expected)


def test_backward_dates_with_eom_adjustment():
    print(
        "Testing that the first date is not adjusted for EOM going backward when termination date convention is unadjusted...")

    schedule = MakeSchedule().begin(datetime(1996, 8, 22)).end(datetime(1997, 8, 31)).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_tenor(
        Period(6, TimeUnit.Months)).with_convention(
        BusinessDayConvention.Unadjusted).with_termination_date_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month().schedule()

    expected = [datetime(1996, 8, 22)]
    expected.append(datetime(1996, 8, 31))
    expected.append(datetime(1997, 2, 28))
    expected.append(datetime(1997, 8, 31))

    check_dates(schedule, expected)


def test_double_first_date_with_eom_adjustment():
    print("Testing that the first date is not duplicated due to EOM convention when going backwards...")

    schedule = MakeSchedule().begin(datetime(1996, 8, 22)).end(datetime(1997, 8, 31)).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_tenor(
        Period(6, TimeUnit.Months)).with_convention(
        BusinessDayConvention.Following).with_termination_date_convention(
        BusinessDayConvention.Following).backwards().end_of_month().schedule()

    expected = [datetime(1996, 8, 30)]
    expected.append(datetime(1997, 2, 28))
    expected.append(datetime(1997, 8, 29))

    check_dates(schedule, expected)


def test_date_constructor():
    print("Testing the constructor taking a vector of dates and possibly additional meta information...")

    dates = [datetime(2015, 5, 16),
             datetime(2015, 5, 18),
             datetime(2016, 5, 18),
             datetime(2017, 12, 31)]

    # schedule without any additional information
    schedule1 = Schedule(dates=dates)
    if schedule1.size() != len(dates):
        raise TestError(f"schedule1 has size {schedule1.size()} , expected {len(dates)}")

    for i in range(len(dates)):
        if schedule1[i] != dates[i]:
            raise TestError(f"schedule1 has {schedule1[i]}  at position {i} , expected {dates[i]}")

    if schedule1.calendar != NullCalendar():
        raise TestError(f"schedule1 has calendar {schedule1.calendar().name()}, expected null calendar""")

    if schedule1.convention != BusinessDayConvention.Unadjusted:
        raise TestError(f"schedule1 has convention {schedule1.convention}, expected unadjusted""")

    # schedule with metadata
    regular = [False, True, False]
    schedule2 = Schedule(dates=dates,
                         calendar=TARGET(),
                         convention=BusinessDayConvention.Following,
                         termination_date_convention=BusinessDayConvention.Modified_Preceding,
                         tenor=Period(1, TimeUnit.Years),
                         rule=DateGenerationTypes.Backward,
                         end_of_month=True,
                         is_regular=regular)
    for i in range(1, len(dates)):
        if schedule2.is_regular(i) != regular[i - 1]:
            raise TestError(
                f"schedule2 has a {schedule2.is_regular(i)} period at position {i}, expected {regular[i - 1]} """)

    if schedule2.calendar != TARGET():
        raise TestError(f"schedule2 has calendar {schedule2.calendar().name()}, expected TARGET""")

    if schedule2.convention != BusinessDayConvention.Following:
        raise TestError(f"schedule2 has convention {schedule2.convention}, expected Following""")

    if schedule2.termination_date_convention_ != BusinessDayConvention.Modified_Preceding:
        raise TestError(
            f"schedule2 has convention {schedule2.termination_date_convention_}, expected Modified Preceding""")

    if schedule2.tenor() != Period(1, TimeUnit.Years):
        raise TestError(f"schedule2 has tenor {schedule2.tenor()}, expected 1Y""")

    if schedule2.rule() != DateGenerationTypes.Backward:
        raise TestError(f"schedule2 has rule {schedule2.rule()}, expected Backward""")

    if not schedule2.end_of_month():
        raise TestError(f"schedule2 has end of month flag false, expected true""")


def test_four_weeks_tenor():
    print("Testing that a four-weeks tenor works...")

    try:
        schedule = MakeSchedule().begin(datetime(2016, 1, 13)).end(datetime(2016, 5, 4)).with_calendar(
            TARGET()).with_tenor(Period(4, TimeUnit.Weeks)).with_convention(
            BusinessDayConvention.Following).forwards().schedule()
    except QTError as e:
        err_msg = e.__repr__()
        raise TestError(f"A four-weeks tenor caused an exception: {err_msg}")


def test_schedule_always_has_a_start_date():
    print("Testing that variations of MakeSchedule always produce a schedule with a start date...")

    # Attempt to establish whether the first coupon payment date is always the second element of the constructor.

    calendar = UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)
    schedule = MakeSchedule().begin(datetime(2017, 1, 10)).with_first_date(datetime(2017, 8, 31)).end(
        datetime(2026, 2, 28)).with_frequency(Frequency.Semiannual).with_calendar(
        calendar).with_convention(BusinessDayConvention.Unadjusted).backwards().end_of_month(False).schedule()

    assert schedule.dates[0] == datetime(2017, 1, 10), "The first element should always be the start date"

    schedule = MakeSchedule().begin(datetime(2017, 1, 10)).end(datetime(2026, 2, 28)).with_frequency(
        Frequency.Semiannual).with_calendar(calendar).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month(False).schedule()
    assert schedule.dates[0] == datetime(2017, 1, 10), "The first element should always be the start date"

    schedule = MakeSchedule().begin(datetime(2017, 8, 31)).end(datetime(2026, 2, 28)).with_frequency(
        Frequency.Semiannual).with_calendar(calendar).with_convention(
        BusinessDayConvention.Unadjusted).backwards().end_of_month(False).schedule()
    assert schedule.dates[0] == datetime(2017, 8, 31), "The first element should always be the start date"


def test_short_eom_schedule():
    print("Testing short end-of-month schedule...")
    try:
        schedule = MakeSchedule().begin(datetime(2019, 2, 21)).end(datetime(2019, 2, 28)).with_calendar(
            TARGET()).with_tenor(Period(1, TimeUnit.Years)).with_convention(
            BusinessDayConvention.Modified_Following).with_termination_date_convention(
            BusinessDayConvention.Modified_Following).backwards().end_of_month(True).schedule()
    except Exception as e:
        logger.error(e)
    else:
        logger.info("successful")

    qt_require(schedule.size() == 2, 'require schedule.size() == 2')
    try:
        assert schedule[0] == datetime(2019, 2, 21), 'check schedule[0] == datetime(2019, 2, 21) has failed'
    except Exception as e:
        logger.error(e)
    try:
        assert schedule[1] == datetime(2019, 2, 28), 'check schedule[0] == datetime(2019, 2, 28) has failed'
    except Exception as e:
        logger.error(e)


def test_first_date_on_maturity():
    print("Testing schedule with first date on maturity...")

    schedule = MakeSchedule().begin(datetime(2016, 9, 20)).end(datetime(2016, 12, 20)).with_first_date(
        datetime(2016, 12, 20)).with_frequency(Frequency.Quarterly).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_convention(
        BusinessDayConvention.Unadjusted).backwards().schedule()

    expected = [datetime(2016, 9, 20),
                datetime(2016, 12, 20)]

    check_dates(schedule, expected)

    schedule = MakeSchedule().begin(datetime(2016, 9, 20)).end(datetime(2016, 12, 20)).with_first_date(
        datetime(2016, 12, 20)).with_frequency(Frequency.Quarterly).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_convention(
        BusinessDayConvention.Unadjusted).forwards().schedule()

    check_dates(schedule, expected)


def test_next_to_last_date_on_start():
    print("Testing schedule with next-to-last date on start date...")

    schedule = MakeSchedule().begin(datetime(2016, 9, 20)).end(datetime(2016, 12, 20)).with_next_to_last_date(
        datetime(2016, 9, 20)).with_frequency(Frequency.Quarterly).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_convention(
        BusinessDayConvention.Unadjusted).backwards().schedule()

    expected = [datetime(2016, 9, 20),
                datetime(2016, 12, 20)]

    check_dates(schedule, expected)

    schedule = MakeSchedule().begin(datetime(2016, 9, 20)).end(datetime(2016, 12, 20)).with_next_to_last_date(
        datetime(2016, 9, 20)).with_frequency(Frequency.Quarterly).with_calendar(
        UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)).with_convention(
        BusinessDayConvention.Unadjusted).backwards().schedule()

    check_dates(schedule, expected)


def test_truncation():
    print("Testing schedule truncation...")

    schedule = MakeSchedule().begin(datetime(2009, 9, 30)).end(datetime(2020, 6, 15)).with_calendar(Japan()).with_tenor(
        Period(6, TimeUnit.Months)).with_convention(BusinessDayConvention.Following).with_termination_date_convention(
        BusinessDayConvention.Following).forwards().end_of_month().schedule()

    # Until
    t = schedule.until(datetime(2014, 1, 1))
    expected = [datetime(2009, 9, 30)]
    expected.append(datetime(2010, 3, 31))
    expected.append(datetime(2010, 9, 30))
    expected.append(datetime(2011, 3, 31))
    expected.append(datetime(2011, 9, 30))
    expected.append(datetime(2012, 3, 30))
    expected.append(datetime(2012, 9, 28))
    expected.append(datetime(2013, 3, 29))
    expected.append(datetime(2013, 9, 30))
    expected.append(datetime(2014, 1, 1))
    check_dates(t, expected)
    try:
        assert not t.is_regular()[-1], 'check t.is_regular()[-1] == False has failed'
    except Exception as e:
        logger.error(e)

    #  Until, with truncation date falling on a schedule date
    t = schedule.until(datetime(2013, 9, 30))
    expected = [datetime(2009, 9, 30)]
    expected.append(datetime(2010, 3, 31))
    expected.append(datetime(2010, 9, 30))
    expected.append(datetime(2011, 3, 31))
    expected.append(datetime(2011, 9, 30))
    expected.append(datetime(2012, 3, 30))
    expected.append(datetime(2012, 9, 28))
    expected.append(datetime(2013, 3, 29))
    expected.append(datetime(2013, 9, 30))
    check_dates(t, expected)
    try:
        assert t.is_regular()[-1], 'check t.is_regular()[-1] == False has failed'
    except Exception as e:
        logger.error(e)

    # After
    t = schedule.after(datetime(2014, 1, 1))
    expected = [datetime(2014, 1, 1)]
    expected.append(datetime(2014, 3, 31))
    expected.append(datetime(2014, 9, 30))
    expected.append(datetime(2015, 3, 31))
    expected.append(datetime(2015, 9, 30))
    expected.append(datetime(2016, 3, 31))
    expected.append(datetime(2016, 9, 30))
    expected.append(datetime(2017, 3, 31))
    expected.append(datetime(2017, 9, 29))
    expected.append(datetime(2018, 3, 30))
    expected.append(datetime(2018, 9, 28))
    expected.append(datetime(2019, 3, 29))
    expected.append(datetime(2019, 9, 30))
    expected.append(datetime(2020, 3, 31))
    expected.append(datetime(2020, 6, 30))
    check_dates(t, expected)
    try:
        assert not t.is_regular()[0], 'check t.is_regular()[-1] == False has failed'
    except Exception as e:
        logger.error(e)

    # After, with truncation date falling on a schedule date
    t = schedule.after(datetime(2018, 9, 28))
    expected = [datetime(2018, 9, 28)]
    expected.append(datetime(2019, 3, 29))
    expected.append(datetime(2019, 9, 30))
    expected.append(datetime(2020, 3, 31))
    expected.append(datetime(2020, 6, 30))
    check_dates(t, expected)
    try:
        assert t.is_regular()[0], 'check t.is_regular()[-1] == False has failed'
    except Exception as e:
        logger.error(e)
