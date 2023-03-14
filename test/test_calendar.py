from datetime import datetime, timedelta

from qtmodel.error import TestError, qt_require
from qtmodel.settings import Settings
from qtmodel.time.calendar import CalendarTypes
from qtmodel.time.calendars.jointcalendar import JointCalendar, JointCalendarRule
from qtmodel.time.date import DateTool
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.calendars.china import China
from qtmodel.time.calendars.target import TARGET
from qtmodel.time.calendars.unitedstates import UnitedStates
from qtmodel.time.calendars.brazil import Brazil
from qtmodel.time.calendars.bespokecalendar import BespokeCalendar
from qtmodel.time.weekday import Weekday


def test_modified_calendars():
    print("Testing Testing calendar modification...")

    calendar1 = TARGET()
    calendar2 = UnitedStates(CalendarTypes.UNITED_STATES_NYSE)
    date1 = datetime(2004, 5, 1)  # holiday for both calendars
    date2 = datetime(2004, 4, 26)  # business day
    qt_require(calendar1.is_holiday(date1), "wrong assumption---correct the test")
    qt_require(calendar1.is_business_day(date2), "wrong assumption---correct the test")
    qt_require(calendar2.is_holiday(date1), "wrong assumption---correct the test")
    qt_require(calendar2.is_business_day(date2), "wrong assumption---correct the test")

    #  modify the TARGET calendar
    calendar1.remove_holiday(date1)
    calendar1.add_holiday(date2)

    # test
    added_holidays = set(calendar1.added_holidays)
    removed_holidays = set(calendar1.removed_holidays)
    qt_require(date1 not in added_holidays, "did not expect to find date in added_holidays")
    qt_require(date2 in added_holidays, "expected to find date in added_holidays")
    qt_require(date1 in removed_holidays, "expected to find date in removed_holidays")
    qt_require(date2 not in removed_holidays, "did not expect to find date in removed_holidays")

    if calendar1.is_holiday(date1):
        raise TestError(f"{date1} still a holiday for original TARGET instance")
    if calendar1.is_business_day(date2):
        raise TestError(f"{date2} still a business for original TARGET instance")

    #  any instance of TARGET should be modified...
    calendar3 = TARGET()
    if calendar3.is_holiday(date1):
        raise TestError(f"{date1} still a holiday for generic TARGET instance")
    if calendar3.is_business_day(date2):
        raise TestError(f"{date2} still a business for generic TARGET instance")

    #  ...but not other calendars
    if calendar2.is_business_day(date1):
        raise TestError(f"{date1} business day for New York")
    if calendar2.is_holiday(date2):
        raise TestError(f"{date2} holiday for New York")

    #  restore original holiday set---test the other way around
    calendar3.add_holiday(date1)
    calendar3.remove_holiday(date2)
    if calendar1.is_business_day(date1):
        raise TestError(f"{date1} still a business day")
    if calendar1.is_holiday(date2):
        raise TestError(f"{date2} still a holiday")


def test_joint_calendars():
    print("Testing joint calendars...")

    calendar1 = TARGET()
    calendar2 = China(CalendarTypes.CHINA_SSE)
    calendar3 = UnitedStates(CalendarTypes.UNITED_STATES_NYSE)
    calendar4 = Brazil()

    calendar_vect = [calendar1, calendar2, calendar3, calendar4]
    c12h = JointCalendar([calendar1, calendar2], JointCalendarRule.JoinHolidays)
    c12b = JointCalendar([calendar1, calendar2], JointCalendarRule.JoinBusinessDays)
    c123h = JointCalendar([calendar1, calendar2, calendar3], JointCalendarRule.JoinHolidays)
    c123b = JointCalendar([calendar1, calendar2, calendar3], JointCalendarRule.JoinBusinessDays)
    cvh = JointCalendar(calendar_vect, JointCalendarRule.JoinHolidays)

    # test one year, starting today
    first_date = datetime.today()
    first_date = datetime(first_date.year, first_date.month, first_date.day)
    end_date = DateTool.advance(date=first_date, n=1, units=TimeUnit.Years)
    it_date = first_date
    one_day = timedelta(days=1)
    while it_date < end_date:
        b1 = calendar1.is_business_day(it_date)
        b2 = calendar2.is_business_day(it_date)
        b3 = calendar3.is_business_day(it_date)
        b4 = calendar4.is_business_day(it_date)
        if (b1 and b2) != c12h.is_business_day(it_date):
            raise TestError(
                f"At date {it_date} inconsistency between joint calendar {c12h.name()} (joining holidays) and its components")

        if (b1 or b2) != c12b.is_business_day(it_date):
            raise TestError(
                f"At date {it_date} inconsistency between joint calendar {c12b.name()} (joining business days) and its components")

        if (b1 and b2 and b3) != c123h.is_business_day(it_date):
            raise TestError(
                f"At date {it_date} inconsistency between joint calendar {c123h.name()} (joining holidays) and its components")

        if (b1 or b2 or b3) != c123b.is_business_day(it_date):
            raise TestError(
                f"At date {it_date} inconsistency between joint calendar {c123b.name()} (joining business days) and its components")

        if (b1 and b2 and b3 and b4) != cvh.is_business_day(it_date):
            raise TestError(
                f"At date {it_date} inconsistency between joint calendar {cvh.name()} (joining business days) and its components")

        it_date += one_day


def test_US_settlement():
    print("Testing US settlement holiday list...")

    expected_hol = [datetime(2004, 1, 1)]
    expected_hol.append(datetime(2004, 1, 19))
    expected_hol.append(datetime(2004, 2, 16))
    expected_hol.append(datetime(2004, 5, 31))
    expected_hol.append(datetime(2004, 7, 5))
    expected_hol.append(datetime(2004, 9, 6))
    expected_hol.append(datetime(2004, 10, 11))
    expected_hol.append(datetime(2004, 11, 11))
    expected_hol.append(datetime(2004, 11, 25))
    expected_hol.append(datetime(2004, 12, 24))

    expected_hol.append(datetime(2004, 12, 31))
    expected_hol.append(datetime(2005, 1, 17))
    expected_hol.append(datetime(2005, 2, 21))
    expected_hol.append(datetime(2005, 5, 30))
    expected_hol.append(datetime(2005, 7, 4))
    expected_hol.append(datetime(2005, 9, 5))
    expected_hol.append(datetime(2005, 10, 10))
    expected_hol.append(datetime(2005, 11, 11))
    expected_hol.append(datetime(2005, 11, 24))
    expected_hol.append(datetime(2005, 12, 26))

    calendar = UnitedStates(CalendarTypes.UNITED_STATES_SETTLEMENT)
    hol = calendar.holiday_list(datetime(2004, 1, 1), datetime(2005, 12, 31))
    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")

    for i in range(len(hol)):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")

    #  before Uniform Monday Holiday Act

    expected_hol = [datetime(1961, 1, 2)]
    expected_hol.append(datetime(1961, 2, 22))
    expected_hol.append(datetime(1961, 5, 30))
    expected_hol.append(datetime(1961, 7, 4))
    expected_hol.append(datetime(1961, 9, 4))
    expected_hol.append(datetime(1961, 11, 10))
    expected_hol.append(datetime(1961, 11, 23))
    expected_hol.append(datetime(1961, 12, 25))

    hol = calendar.holiday_list(datetime(1961, 1, 1), datetime(1961, 12, 31))
    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")

    for i in range(len(hol)):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")


def test_US_government_bond_market():
    print("Testing US government bond market holiday list...")

    expected_hol = [datetime(2004, 1, 1)]
    expected_hol.append(datetime(2004, 1, 19))
    expected_hol.append(datetime(2004, 2, 16))
    expected_hol.append(datetime(2004, 4, 9))
    expected_hol.append(datetime(2004, 5, 31))
    expected_hol.append(datetime(2004, 6, 11))
    expected_hol.append(datetime(2004, 7, 5))
    expected_hol.append(datetime(2004, 9, 6))
    expected_hol.append(datetime(2004, 10, 11))
    expected_hol.append(datetime(2004, 11, 11))
    expected_hol.append(datetime(2004, 11, 25))
    expected_hol.append(datetime(2004, 12, 24))

    calendar = UnitedStates(CalendarTypes.UNITED_STATES_GOVERNMENT_BOND)
    hol = calendar.holiday_list(datetime(2004, 1, 1), datetime(2004, 12, 31))
    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")

    for i in range(len(hol)):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")


def test_US_New_York_Stock_Exchange():
    print("Testing New York Stock Exchange holiday list...")

    expected_hol = [datetime(2004, 1, 1)]
    expected_hol.append(datetime(2004, 1, 19))
    expected_hol.append(datetime(2004, 2, 16))
    expected_hol.append(datetime(2004, 4, 9))
    expected_hol.append(datetime(2004, 5, 31))
    expected_hol.append(datetime(2004, 6, 11))
    expected_hol.append(datetime(2004, 7, 5))
    expected_hol.append(datetime(2004, 9, 6))
    expected_hol.append(datetime(2004, 11, 25))
    expected_hol.append(datetime(2004, 12, 24))

    expected_hol.append(datetime(2005, 1, 17))
    expected_hol.append(datetime(2005, 2, 21))
    expected_hol.append(datetime(2005, 3, 25))
    expected_hol.append(datetime(2005, 5, 30))
    expected_hol.append(datetime(2005, 7, 4))
    expected_hol.append(datetime(2005, 9, 5))
    expected_hol.append(datetime(2005, 11, 24))
    expected_hol.append(datetime(2005, 12, 26))

    expected_hol.append(datetime(2006, 1, 2))
    expected_hol.append(datetime(2006, 1, 16))
    expected_hol.append(datetime(2006, 2, 20))
    expected_hol.append(datetime(2006, 4, 14))
    expected_hol.append(datetime(2006, 5, 29))
    expected_hol.append(datetime(2006, 7, 4))
    expected_hol.append(datetime(2006, 9, 4))
    expected_hol.append(datetime(2006, 11, 23))
    expected_hol.append(datetime(2006, 12, 25))

    calendar = UnitedStates(CalendarTypes.UNITED_STATES_NYSE)
    hol = calendar.holiday_list(datetime(2004, 1, 1), datetime(2006, 12, 31))
    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")

    for i in range(len(hol)):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")

    hist_close = [datetime(2012, 10, 30)]  # Hurricane Sandy
    hist_close.append(datetime(2012, 10, 29))  # Hurricane Sandy
    hist_close.append(datetime(2004, 6, 11))  # Reagan's funeral
    hist_close.append(datetime(2001, 9, 14))  # September 14, 2001
    hist_close.append(datetime(2001, 9, 13))  # September 13, 2001
    hist_close.append(datetime(2001, 9, 12))  # September 12, 2001
    hist_close.append(datetime(2001, 9, 11))  # September 11, 2001
    hist_close.append(datetime(1994, 4, 27))  # Nixon's funeral.
    hist_close.append(datetime(1985, 9, 27))  # Hurricane Gloria
    hist_close.append(datetime(1977, 7, 14))  # 1977 Blackout
    hist_close.append(datetime(1973, 1, 25))  # Johnson's funeral.
    hist_close.append(datetime(1972, 12, 28))  # Truman's funeral
    hist_close.append(datetime(1969, 7, 21))  # Lunar exploration nat. day
    hist_close.append(datetime(1969, 3, 31))  # Eisenhower's funeral
    hist_close.append(datetime(1969, 2, 10))  # heavy snow
    hist_close.append(datetime(1968, 7, 5))  # Day after Independence Day
    hist_close.append(datetime(1968, 4, 9))  # Mourning for MLK
    hist_close.append(datetime(1965, 12, 24))  # Christmas Eve
    hist_close.append(datetime(1963, 11, 25))  # Kennedy's funeral
    hist_close.append(datetime(1961, 5, 29))  # Day before Decoration Day
    hist_close.append(datetime(1958, 12, 26))  # Day after Christmas
    hist_close.append(datetime(1956, 12, 24))  # Christmas Eve
    hist_close.append(datetime(1954, 12, 24))  # Christmas Eve
    # June 12-Dec. 31, 1968
    # Four day week (closed on Wednesdays) - Paperwork Crisis
    hist_close.append(datetime(1968, 6, 12))
    hist_close.append(datetime(1968, 6, 19))
    hist_close.append(datetime(1968, 6, 26))
    hist_close.append(datetime(1968, 7, 3))
    hist_close.append(datetime(1968, 7, 10))
    hist_close.append(datetime(1968, 7, 17))
    hist_close.append(datetime(1968, 11, 20))
    hist_close.append(datetime(1968, 12, 4))
    hist_close.append(datetime(1968, 11, 27))
    hist_close.append(datetime(1968, 12, 11))
    hist_close.append(datetime(1968, 12, 18))
    # Presidential election days
    hist_close.append(datetime(1980, 11, 4))
    hist_close.append(datetime(1976, 11, 2))
    hist_close.append(datetime(1976, 11, 2))
    hist_close.append(datetime(1968, 11, 5))
    hist_close.append(datetime(1964, 11, 3))
    for i in range(len(hist_close)):
        if not calendar.is_holiday(hist_close[i]):
            raise TestError(
                f"{hist_close[i]}should be holiday (historical close)")


def test_TARGET():
    print("Testing TARGET holiday list...")
    expected_hol = [datetime(1999, 1, 1)]
    expected_hol.append(datetime(1999, 12, 31))

    expected_hol.append(datetime(2000, 4, 21))
    expected_hol.append(datetime(2000, 4, 24))
    expected_hol.append(datetime(2000, 5, 1))
    expected_hol.append(datetime(2000, 12, 25))
    expected_hol.append(datetime(2000, 12, 26))

    expected_hol.append(datetime(2001, 1, 1))
    expected_hol.append(datetime(2001, 4, 13))
    expected_hol.append(datetime(2001, 4, 16))
    expected_hol.append(datetime(2001, 5, 1))
    expected_hol.append(datetime(2001, 12, 25))
    expected_hol.append(datetime(2001, 12, 26))
    expected_hol.append(datetime(2001, 12, 31))

    expected_hol.append(datetime(2002, 1, 1))
    expected_hol.append(datetime(2002, 3, 29))
    expected_hol.append(datetime(2002, 4, 1))
    expected_hol.append(datetime(2002, 5, 1))
    expected_hol.append(datetime(2002, 12, 25))
    expected_hol.append(datetime(2002, 12, 26))

    expected_hol.append(datetime(2003, 1, 1))
    expected_hol.append(datetime(2003, 4, 18))
    expected_hol.append(datetime(2003, 4, 21))
    expected_hol.append(datetime(2003, 5, 1))
    expected_hol.append(datetime(2003, 12, 25))
    expected_hol.append(datetime(2003, 12, 26))

    expected_hol.append(datetime(2004, 1, 1))
    expected_hol.append(datetime(2004, 4, 9))
    expected_hol.append(datetime(2004, 4, 12))

    expected_hol.append(datetime(2005, 3, 25))
    expected_hol.append(datetime(2005, 3, 28))
    expected_hol.append(datetime(2005, 12, 26))

    expected_hol.append(datetime(2006, 4, 14))
    expected_hol.append(datetime(2006, 4, 17))
    expected_hol.append(datetime(2006, 5, 1))
    expected_hol.append(datetime(2006, 12, 25))
    expected_hol.append(datetime(2006, 12, 26))

    calendar = TARGET()
    hol = calendar.holiday_list(datetime(1999, 1, 1), datetime(2006, 12, 31))

    for i in range(0, min(len(hol), len(expected_hol))):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")

    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")


def test_Brazil():
    print("Testing Brazil holiday list...")

    # expectedHol.push_back(Date(1,January,2005)); // Saturday
    expected_hol = [datetime(2005, 2, 7)]
    expected_hol.append(datetime(2005, 2, 8))
    expected_hol.append(datetime(2005, 3, 25))
    expected_hol.append(datetime(2005, 4, 21))

    # expectedHol.push_back(Date(1,May,2005)); // Sunday
    expected_hol.append(datetime(2005, 5, 26))
    expected_hol.append(datetime(2005, 9, 7))
    expected_hol.append(datetime(2005, 10, 12))
    expected_hol.append(datetime(2005, 11, 2))
    expected_hol.append(datetime(2005, 11, 15))
    # expectedHol.push_back(Date(25,December,2005)); // Sunday

    # expectedHol.push_back(Date(1,January,2006)); // Sunday
    expected_hol.append(datetime(2006, 2, 27))
    expected_hol.append(datetime(2006, 2, 28))
    expected_hol.append(datetime(2006, 4, 14))
    expected_hol.append(datetime(2006, 4, 21))
    expected_hol.append(datetime(2006, 5, 1))
    expected_hol.append(datetime(2006, 6, 15))
    expected_hol.append(datetime(2006, 9, 7))
    expected_hol.append(datetime(2006, 10, 12))
    expected_hol.append(datetime(2006, 11, 2))
    expected_hol.append(datetime(2006, 11, 15))
    expected_hol.append(datetime(2006, 12, 25))

    calendar = Brazil()
    hol = calendar.holiday_list(datetime(2005, 1, 1), datetime(2006, 12, 31))

    for i in range(0, min(len(hol), len(expected_hol))):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")

    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")

def test_China_SSE():
    print("Testing China Shanghai Stock Exchange holiday list...")

    # China Shanghai Securities Exchange holiday list in the year 2014
    expected_hol = [datetime(2014, 1, 1)]
    expected_hol.append(datetime(2014, 1, 31))
    expected_hol.append(datetime(2014, 2, 3))
    expected_hol.append(datetime(2014, 2, 4))
    expected_hol.append(datetime(2014, 2, 5))
    expected_hol.append(datetime(2014, 2, 6))
    expected_hol.append(datetime(2014, 4, 7))
    expected_hol.append(datetime(2014, 5, 1))
    expected_hol.append(datetime(2014, 5, 2))
    expected_hol.append(datetime(2014, 6, 2))
    expected_hol.append(datetime(2014, 9, 8))
    expected_hol.append(datetime(2014, 10, 1))
    expected_hol.append(datetime(2014, 10, 2))
    expected_hol.append(datetime(2014, 10, 3))
    expected_hol.append(datetime(2014, 10, 6))
    expected_hol.append(datetime(2014, 10, 7))

    # China Shanghai Securities Exchange holiday list in the year 2015
    expected_hol.append(datetime(2015, 1, 1))
    expected_hol.append(datetime(2015, 1, 2))
    expected_hol.append(datetime(2015, 2, 18))
    expected_hol.append(datetime(2015, 2, 19))
    expected_hol.append(datetime(2015, 2, 20))
    expected_hol.append(datetime(2015, 2, 23))
    expected_hol.append(datetime(2015, 2, 24))
    expected_hol.append(datetime(2015, 4, 6))
    expected_hol.append(datetime(2015, 5, 1))
    expected_hol.append(datetime(2015, 6, 22))
    expected_hol.append(datetime(2015, 9, 3))
    expected_hol.append(datetime(2015, 9, 4))
    expected_hol.append(datetime(2015, 10, 1))
    expected_hol.append(datetime(2015, 10, 2))
    expected_hol.append(datetime(2015, 10, 5))
    expected_hol.append(datetime(2015, 10, 6))
    expected_hol.append(datetime(2015, 10, 7))

    # China Shanghai Securities Exchange holiday list in the year 2016
    expected_hol.append(datetime(2016, 1, 1))
    expected_hol.append(datetime(2016, 2, 8))
    expected_hol.append(datetime(2016, 2, 9))
    expected_hol.append(datetime(2016, 2, 10))
    expected_hol.append(datetime(2016, 2, 11))
    expected_hol.append(datetime(2016, 2, 12))
    expected_hol.append(datetime(2016, 4, 4))
    expected_hol.append(datetime(2016, 5, 2))
    expected_hol.append(datetime(2016, 6, 9))
    expected_hol.append(datetime(2016, 6, 10))
    expected_hol.append(datetime(2016, 9, 15))
    expected_hol.append(datetime(2016, 9, 16))
    expected_hol.append(datetime(2016, 10, 3))
    expected_hol.append(datetime(2016, 10, 4))
    expected_hol.append(datetime(2016, 10, 5))
    expected_hol.append(datetime(2016, 10, 6))
    expected_hol.append(datetime(2016, 10, 7))

    # China Shanghai Securities Exchange holiday list in the year 2017
    expected_hol.append(datetime(2017, 1, 2))
    expected_hol.append(datetime(2017, 1, 27))
    expected_hol.append(datetime(2017, 1, 30))
    expected_hol.append(datetime(2017, 1, 31))
    expected_hol.append(datetime(2017, 2, 1))
    expected_hol.append(datetime(2017, 2, 2))
    expected_hol.append(datetime(2017, 4, 3))
    expected_hol.append(datetime(2017, 4, 4))
    expected_hol.append(datetime(2017, 5, 1))
    expected_hol.append(datetime(2017, 5, 29))
    expected_hol.append(datetime(2017, 5, 30))
    expected_hol.append(datetime(2017, 10, 2))
    expected_hol.append(datetime(2017, 10, 3))
    expected_hol.append(datetime(2017, 10, 4))
    expected_hol.append(datetime(2017, 10, 5))
    expected_hol.append(datetime(2017, 10, 6))

    # China Shanghai Securities Exchange holiday list in the year 2018
    expected_hol.append(datetime(2018, 1, 1))
    expected_hol.append(datetime(2018, 2, 15))
    expected_hol.append(datetime(2018, 2, 16))
    expected_hol.append(datetime(2018, 2, 19))
    expected_hol.append(datetime(2018, 2, 20))
    expected_hol.append(datetime(2018, 2, 21))
    expected_hol.append(datetime(2018, 4, 5))
    expected_hol.append(datetime(2018, 4, 6))
    expected_hol.append(datetime(2018, 4, 30))
    expected_hol.append(datetime(2018, 5, 1))
    expected_hol.append(datetime(2018, 6, 18))
    expected_hol.append(datetime(2018, 9, 24))
    expected_hol.append(datetime(2018, 10, 1))
    expected_hol.append(datetime(2018, 10, 2))
    expected_hol.append(datetime(2018, 10, 3))
    expected_hol.append(datetime(2018, 10, 4))
    expected_hol.append(datetime(2018, 10, 5))
    expected_hol.append(datetime(2018, 12, 31))

    # China Shanghai Securities Exchange holiday list in the year 2019
    expected_hol.append(datetime(2019, 1, 1))
    expected_hol.append(datetime(2019, 2, 4))
    expected_hol.append(datetime(2019, 2, 5))
    expected_hol.append(datetime(2019, 2, 6))
    expected_hol.append(datetime(2019, 2, 7))
    expected_hol.append(datetime(2019, 2, 8))
    expected_hol.append(datetime(2019, 4, 5))
    expected_hol.append(datetime(2019, 5, 1))
    expected_hol.append(datetime(2019, 5, 2))
    expected_hol.append(datetime(2019, 5, 3))
    expected_hol.append(datetime(2019, 6, 7))
    expected_hol.append(datetime(2019, 9, 13))
    expected_hol.append(datetime(2019, 10, 1))
    expected_hol.append(datetime(2019, 10, 2))
    expected_hol.append(datetime(2019, 10, 3))
    expected_hol.append(datetime(2019, 10, 4))
    expected_hol.append(datetime(2019, 10, 7))

    # China Shanghai Securities Exchange holiday list in the year 2020
    expected_hol.append(datetime(2020, 1, 1))
    expected_hol.append(datetime(2020, 1, 24))
    expected_hol.append(datetime(2020, 1, 27))
    expected_hol.append(datetime(2020, 1, 28))
    expected_hol.append(datetime(2020, 1, 29))
    expected_hol.append(datetime(2020, 1, 30))
    expected_hol.append(datetime(2020, 1, 31))
    expected_hol.append(datetime(2020, 4, 6))
    expected_hol.append(datetime(2020, 5, 1))
    expected_hol.append(datetime(2020, 5, 4))
    expected_hol.append(datetime(2020, 5, 5))
    expected_hol.append(datetime(2020, 6, 25))
    expected_hol.append(datetime(2020, 6, 26))
    expected_hol.append(datetime(2020, 10, 1))
    expected_hol.append(datetime(2020, 10, 2))
    expected_hol.append(datetime(2020, 10, 5))
    expected_hol.append(datetime(2020, 10, 6))
    expected_hol.append(datetime(2020, 10, 7))
    expected_hol.append(datetime(2020, 10, 8))

    # China Shanghai Securities Exchange holiday list in the year 2021
    expected_hol.append(datetime(2021, 1, 1))
    expected_hol.append(datetime(2021, 2, 11))
    expected_hol.append(datetime(2021, 2, 12))
    expected_hol.append(datetime(2021, 2, 15))
    expected_hol.append(datetime(2021, 2, 16))
    expected_hol.append(datetime(2021, 2, 17))
    expected_hol.append(datetime(2021, 4, 5))
    expected_hol.append(datetime(2021, 5, 3))
    expected_hol.append(datetime(2021, 5, 4))
    expected_hol.append(datetime(2021, 5, 5))
    expected_hol.append(datetime(2021, 6, 14))
    expected_hol.append(datetime(2021, 9, 20))
    expected_hol.append(datetime(2021, 9, 21))
    expected_hol.append(datetime(2021, 10, 1))
    expected_hol.append(datetime(2021, 10, 4))
    expected_hol.append(datetime(2021, 10, 5))
    expected_hol.append(datetime(2021, 10, 6))
    expected_hol.append(datetime(2021, 10, 7))

    # China Shanghai Securities Exchange holiday list in the year 2022
    expected_hol.append(datetime(2022, 1, 3))
    expected_hol.append(datetime(2022, 1, 31))
    expected_hol.append(datetime(2022, 2, 1))
    expected_hol.append(datetime(2022, 2, 2))
    expected_hol.append(datetime(2022, 2, 3))
    expected_hol.append(datetime(2022, 2, 4))
    expected_hol.append(datetime(2022, 4, 4))
    expected_hol.append(datetime(2022, 4, 5))
    expected_hol.append(datetime(2022, 5, 2))
    expected_hol.append(datetime(2022, 5, 3))
    expected_hol.append(datetime(2022, 5, 4))
    expected_hol.append(datetime(2022, 6, 3))
    expected_hol.append(datetime(2022, 9, 12))
    expected_hol.append(datetime(2022, 10, 3))
    expected_hol.append(datetime(2022, 10, 4))
    expected_hol.append(datetime(2022, 10, 5))
    expected_hol.append(datetime(2022, 10, 6))
    expected_hol.append(datetime(2022, 10, 7))

    calendar = China(CalendarTypes.CHINA_SSE)
    hol = calendar.holiday_list(datetime(2014, 1, 1), datetime(2022, 12, 31))

    for i in range(0, min(len(hol), len(expected_hol))):
        if hol[i] != expected_hol[i]:
            raise TestError(
                f"expected holiday was {expected_hol[i]} while calculated holiday is {hol[i]}")

    if len(hol) != len(expected_hol):
        raise TestError(
            f"there were {len(expected_hol)} expected holidays, while there are {len(hol)} calculated holidays")


def test_China_IB():
    print("Testing China Inter Bank working weekends list..")

    # China Inter Bank working weekends list in the year 2014
    expected_working_weekends = [datetime(2014, 1, 26)]
    expected_working_weekends.append(datetime(2014, 2, 8))
    expected_working_weekends.append(datetime(2014, 5, 4))
    expected_working_weekends.append(datetime(2014, 9, 28))
    expected_working_weekends.append(datetime(2014, 10, 11))

    # China Inter Bank working weekends list in the year 2015
    expected_working_weekends.append(datetime(2015, 1, 4))
    expected_working_weekends.append(datetime(2015, 2, 15))
    expected_working_weekends.append(datetime(2015, 2, 28))
    expected_working_weekends.append(datetime(2015, 9, 6))
    expected_working_weekends.append(datetime(2015, 10, 10))

    # China Inter Bank working weekends list in the year 2016
    expected_working_weekends.append(datetime(2016, 2, 6))
    expected_working_weekends.append(datetime(2016, 2, 14))
    expected_working_weekends.append(datetime(2016, 6, 12))
    expected_working_weekends.append(datetime(2016, 9, 18))
    expected_working_weekends.append(datetime(2016, 10, 8))
    expected_working_weekends.append(datetime(2016, 10, 9))

    # China Inter Bank working weekends list in the year 2017
    expected_working_weekends.append(datetime(2017, 1, 22))
    expected_working_weekends.append(datetime(2017, 2, 4))
    expected_working_weekends.append(datetime(2017, 4, 1))
    expected_working_weekends.append(datetime(2017, 5, 27))
    expected_working_weekends.append(datetime(2017, 9, 30))

    # China Inter Bank working weekends list in the year 2018
    expected_working_weekends.append(datetime(2018, 2, 11))
    expected_working_weekends.append(datetime(2018, 2, 24))
    expected_working_weekends.append(datetime(2018, 4, 8))
    expected_working_weekends.append(datetime(2018, 4, 28))
    expected_working_weekends.append(datetime(2018, 9, 29))
    expected_working_weekends.append(datetime(2018, 9, 30))
    expected_working_weekends.append(datetime(2018, 12, 29))

    # China Inter Bank working weekends list in the year 2019
    expected_working_weekends.append(datetime(2019, 2, 2))
    expected_working_weekends.append(datetime(2019, 2, 3))
    expected_working_weekends.append(datetime(2019, 4, 28))
    expected_working_weekends.append(datetime(2019, 5, 5))
    expected_working_weekends.append(datetime(2019, 9, 29))
    expected_working_weekends.append(datetime(2019, 10, 12))

    # China Inter Bank working weekends list in the year 2020
    expected_working_weekends.append(datetime(2020, 1, 19))
    expected_working_weekends.append(datetime(2020, 4, 26))
    expected_working_weekends.append(datetime(2020, 5, 9))
    expected_working_weekends.append(datetime(2020, 6, 28))
    expected_working_weekends.append(datetime(2020, 9, 27))
    expected_working_weekends.append(datetime(2020, 10, 10))

    # China Inter Bank working weekends list in the year 2021
    expected_working_weekends.append(datetime(2021, 2, 7))
    expected_working_weekends.append(datetime(2021, 2, 20))
    expected_working_weekends.append(datetime(2021, 4, 25))
    expected_working_weekends.append(datetime(2021, 5, 8))
    expected_working_weekends.append(datetime(2021, 9, 18))
    expected_working_weekends.append(datetime(2021, 9, 26))
    expected_working_weekends.append(datetime(2021, 10, 9))

    # China Inter Bank working weekends list in the year 2022
    expected_working_weekends.append(datetime(2022, 1, 29))
    expected_working_weekends.append(datetime(2022, 1, 30))
    expected_working_weekends.append(datetime(2022, 4, 2))
    expected_working_weekends.append(datetime(2022, 4, 24))
    expected_working_weekends.append(datetime(2022, 5, 7))
    expected_working_weekends.append(datetime(2022, 10, 8))
    expected_working_weekends.append(datetime(2022, 10, 9))

    calendar = China(CalendarTypes.CHINA_IB)
    start = datetime(2014, 1, 1)
    end = datetime(2022, 12, 31)
    one_day = timedelta(days=1)
    k = 0
    while start <= end:
        if calendar.is_business_day(start) and calendar.is_weekend(DateTool.weekday(start)):
            if expected_working_weekends[k] != start:
                raise TestError(
                    f"expected working weekend was {expected_working_weekends[k]} while calculated working weekend is {start}")
            k += 1
        start += one_day

    if k != len(expected_working_weekends):
        raise TestError(
            f"there were {len(expected_working_weekends)} expected working weekends, while there are {k} calculated working weekends")


def test_end_of_month():
    print("Testing end-of-month calculation...")
    calendar = TARGET()  # any calendar would be OK
    counter = datetime(1901, 1, 1)
    max_date = datetime(2199, 12, 31)
    last = DateTool.advance(date=max_date, n=-2, units=TimeUnit.Months)
    one_day = timedelta(days=1)

    while counter <= last:
        eom = calendar.end_of_month(counter)
        # check that eom is eom
        if not calendar.is_end_of_month(eom):
            raise TestError(
                f"{eom.weekday(), eom} is not the last business day in {eom.month(), eom.year()} according to {calendar.name()}")
        # check that eom is in the same month as counter
        if eom.month != counter.month:
            raise TestError(f"{eom} is not in the same month as {counter}")
        counter += one_day


def test_business_days_between():
    print("Testing calculation of business days between dates...")

    test_dates = [datetime(2002, 2, 1)]  # is_business_day = true
    test_dates.append(datetime(2002, 2, 4))  # is_business_day = true
    test_dates.append(datetime(2003, 5, 16))  # is_business_day = true
    test_dates.append(datetime(2003, 12, 17))  # is_business_day = true
    test_dates.append(datetime(2004, 12, 17))  # is_business_day = true
    test_dates.append(datetime(2005, 12, 19))  # is_business_day = true
    test_dates.append(datetime(2006, 1, 2))  # is_business_day = true
    test_dates.append(datetime(2006, 3, 13))  # is_business_day = true
    test_dates.append(datetime(2006, 5, 15))  # is_business_day = true
    test_dates.append(datetime(2006, 3, 17))  # is_business_day = true
    test_dates.append(datetime(2006, 5, 15))  # is_business_day = true
    test_dates.append(datetime(2006, 7, 26))  # is_business_day = true
    test_dates.append(datetime(2006, 7, 26))  # is_business_day = true
    test_dates.append(datetime(2006, 7, 27))  # is_business_day = true
    test_dates.append(datetime(2006, 7, 29))  # is_business_day = true
    test_dates.append(datetime(2006, 7, 29))  # is_business_day = true

    # default params: from date included, to excluded
    expected = [1, 321, 152, 251, 252, 10, 48, 42, -38, 38, 51, 0, 1, 2, 0]

    # exclude from, include to
    expected_include_to = [1, 321, 152, 251, 252, 10, 48, 42, -38, 38, 51, 0, 1, 1, 0]

    # include both from and to
    expected_include_all = [2, 322, 153, 252, 253, 11, 49, 43, -39, 39, 52, 1, 2, 2, 0]

    # exclude both from and to
    expected_exclude_all = [0, 320, 151, 250, 251, 9, 47, 41, -37, 37, 50, 0, 0, 1, 0]

    calendar = Brazil()
    for i in range(1, len(test_dates)):
        calculated = calendar.business_days_between(test_dates[i - 1], test_dates[i], True, False)
        if calculated != expected[i - 1]:
            raise TestError(
                f"from {test_dates[i - 1]} included to {test_dates[i]} excluded: calculated {calculated} expected: {expected[i - 1]}")

        calculated = calendar.business_days_between(test_dates[i - 1], test_dates[i], False, True)
        if calculated != expected_include_to[i - 1]:
            raise TestError(
                f"from {test_dates[i - 1]} excluded to {test_dates[i]} included: calculated {calculated} expected: {expected_include_to[i - 1]}")

        calculated = calendar.business_days_between(test_dates[i - 1], test_dates[i], True, True)
        if calculated != expected_include_all[i - 1]:
            raise TestError(
                f"from {test_dates[i - 1]} included to {test_dates[i]} included: calculated {calculated} expected: {expected_include_all[i - 1]}")

        calculated = calendar.business_days_between(test_dates[i - 1], test_dates[i], False, False)
        if calculated != expected_exclude_all[i - 1]:
            raise TestError(
                f"from {test_dates[i - 1]} excluded to {test_dates[i]} excluded: calculated {calculated} expected: {expected_exclude_all[i - 1]}")


def test_bespoke_calendars():
    print("Testing bespoke calendars...")

    a1 = BespokeCalendar()
    b1 = BespokeCalendar()

    test_date1 = datetime(2008, 10, 4)  # Saturday
    test_date2 = datetime(2008, 10, 5)  # Sunday
    test_date3 = datetime(2008, 10, 6)  # Monday
    test_date4 = datetime(2008, 10, 7)  # Tuesday

    if not a1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if not a1.is_business_day(test_date2):
        raise TestError(f"{test_date2} erroneously detected as holiday.")
    if not a1.is_business_day(test_date3):
        raise TestError(f"{test_date3} erroneously detected as holiday.")
    if not a1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    if not b1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if not b1.is_business_day(test_date2):
        raise TestError(f"{test_date2} erroneously detected as holiday.")
    if not b1.is_business_day(test_date3):
        raise TestError(f"{test_date3} erroneously detected as holiday.")
    if not b1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    a1.add_weekend(Weekday.Sunday)
    if not a1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if a1.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if not a1.is_business_day(test_date3):
        raise TestError(f"{test_date3} erroneously detected as holiday.")
    if not a1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    if not b1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if not b1.is_business_day(test_date2):
        raise TestError(f"{test_date2} erroneously detected as holiday.")
    if not b1.is_business_day(test_date3):
        raise TestError(f"{test_date3} erroneously detected as holiday.")
    if not b1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    a1.add_holiday(test_date3)
    if not a1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if a1.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if a1.is_business_day(test_date3):
        raise TestError(f"{test_date3} (marked as holiday) not detected")
    if not a1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    if not b1.is_business_day(test_date1):
        raise TestError(f"{test_date1} erroneously detected as holiday.")
    if not b1.is_business_day(test_date2):
        raise TestError(f"{test_date2} erroneously detected as holiday.")
    if not b1.is_business_day(test_date3):
        raise TestError(f"{test_date3} erroneously detected as holiday.")
    if not b1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    a2 = a1  # linked to a1
    a2.add_weekend(Weekday.Saturday)
    if a1.is_business_day(test_date1):
        raise TestError(f"{test_date1} (Saturday) not detected as weekend.")
    if a1.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if a1.is_business_day(test_date3):
        raise TestError(f"{test_date3} (marked as holiday) not detected")
    if not a1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    if a2.is_business_day(test_date1):
        raise TestError(f"{test_date1} (Saturday) not detected as weekend.")
    if a2.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if a2.is_business_day(test_date3):
        raise TestError(f"{test_date3} (marked as holiday) not detected")
    if not a2.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    a2.add_holiday(test_date4)
    if a1.is_business_day(test_date1):
        raise TestError(f"{test_date1} (Saturday) not detected as weekend.")
    if a1.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if a1.is_business_day(test_date3):
        raise TestError(f"{test_date3} (marked as holiday) not detected")
    if a1.is_business_day(test_date4):
        raise TestError(f"{test_date4} erroneously detected as holiday.")

    if a2.is_business_day(test_date1):
        raise TestError(f"{test_date1} (Saturday) not detected as weekend.")
    if a2.is_business_day(test_date2):
        raise TestError(f"{test_date2} (Sunday) not detected as weekend.")
    if a2.is_business_day(test_date3):
        raise TestError(f"{test_date3} (marked as holiday) not detected")
    if a2.is_business_day(test_date4):
        raise TestError(f"{test_date4} (marked as holiday) not detected")


def test_day_lists():
    print("Testing holidayList and businessDaysList...")
    target = Brazil()
    first_date = Settings().evaluation_date
    end_date = DateTool.advance(date=first_date, n=1, units=TimeUnit.Years)

    # Test that same day holiday_list and business_day_list does not throw an error
    target.holiday_list(first_date, first_date, True)
    target.business_day_list(first_date, first_date)

    holidays = target.holiday_list(first_date, end_date, True)
    business_days = target.business_day_list(first_date, end_date)
    it_holidays = holidays[0]
    it_business_days = business_days[0]
    it_date = first_date
    i = 0
    j = 0
    one_day = timedelta(days=1)
    len_holidays = len(holidays)
    len_business_days = len(business_days)
    while it_date < end_date:
        if i < len_holidays and j < len_business_days and it_date == it_holidays and it_date == it_business_days:
            i += 1
            j += 1
            it_holidays = holidays[i]
            it_business_days = business_days[j]
            raise TestError(f"Date {it_date} is both holiday and business day.")
        elif i < len_holidays and it_date == it_holidays:
            i += 1
            if i == len_holidays - 1:
                break
            it_holidays = holidays[i]
        elif j < len_business_days and it_date == it_business_days:
            j += 1
            if j == len_business_days - 1:
                break
            it_business_days = business_days[j]
        else:
            raise TestError(f"Date {it_date} is neither holiday nor business day.")
        it_date += one_day
