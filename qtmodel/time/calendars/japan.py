from datetime import datetime

from qtmodel.time.calendar import Calendar, CalendarTypes
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday


class Japan(Calendar):
    """
    Japanese calendar
    Holidays:
    Saturdays
    Sundays
    New Year's Day, January 1st
    Bank Holiday, January 2nd
    Bank Holiday, January 3rd
    Coming of Age Day, 2nd Monday in January
    National Foundation Day, February 11th
    Emperor's Birthday, February 23rd since 2020 and December 23rd before
    Vernal Equinox
    Greenery Day, April 29th
    Constitution Memorial Day, May 3rd
    Holiday for a Nation, May 4th
    Children's Day, May 5th
    Marine Day, 3rd Monday in July
    Mountain Day, August 11th (from 2016 onwards)
    Respect for the Aged Day, 3rd Monday in September
    Autumnal Equinox
    Health and Sports Day, 2nd Monday in October
    National Culture Day, November 3rd
    Labor Thanksgiving Day, November 23rd
    Bank Holiday, December 31st
    a few one-shot holidays
    Holidays falling on a Sunday are observed on the Monday following
    except for the bank holidays associated with the new year.
    """
    added_holidays = set()
    removed_holidays = set()

    def __init__(self):
        super().__init__(calendar_type=CalendarTypes.JAPAN)

    def _is_business_day(self, date: datetime) -> bool:
        """
        :param date:
        :return:
        """
        year = date.year
        month = date.month
        weekday = DateTool.weekday(date=date)
        day = date.day
        # equinox calculation
        exact_vernal_equinox_time = 20.69115
        exact_autumnal_equinox_time = 23.09
        diff_per_year = 0.242194
        moving_amount = (year - 2000) * diff_per_year
        number_of_leap_years = (year - 2000) / 4 + \
            (year - 2000) / 100 - (year - 2000) / 400
        ve = int(exact_vernal_equinox_time
                 + moving_amount - number_of_leap_years)  # vernal equinox day
        ae = int(exact_autumnal_equinox_time + moving_amount -
                 number_of_leap_years)  # autumnal equinox day
        # checks
        if (self.is_weekend(weekday)
            # New Year's Day
            or (day == 1 and month == 1)
            # Bank Holiday
            or (day == 2 and month == 1)
            # Bank Holiday
            or (day == 3 and month == 1)
            # Coming of Age Day (2nd Monday in January),
            # was January 15th until 2000
            or (weekday == Weekday.Monday and (8 <= day <= 14) and month == 1
                and year >= 2000)
            or ((day == 15 or (day == 16 and weekday == Weekday.Monday)) and month == 1
                and year < 2000)
            # National Foundation Day
            or ((day == 11 or (day == 12 and weekday == Weekday.Monday)) and month == 2)
            # Emperor's Birthday (Emperor Naruhito)
            or ((day == 23 or (day == 24 and weekday == Weekday.Monday)) and month == 2
                and year >= 2020)
            # Emperor's Birthday (Emperor Akihito)
            or ((day == 23 or (day == 24 and weekday == Weekday.Monday)) and month == 12
                and (1989 <= year < 2019))
            # Vernal Equinox
            or ((day == ve or (day == ve + 1 and weekday == Weekday.Monday)) and month == 3)
            # Greenery Day
            or ((day == 29 or (day == 30 and weekday == Weekday.Monday)) and month == 4)
            # Constitution Memorial Day
            or (day == 3 and month == 5)
            # Holiday for a Nation
            or (day == 4 and month == 5)
            # Children's Day
            or (day == 5 and month == 5)
            # any of the three above observed later if on Saturday or Sunday
            or (day == 6 and month == 5
                and (weekday == Weekday.Monday or weekday == Weekday.Tuesday or weekday == Weekday.Wednesday))
            # Marine Day (3rd Monday in July),
            # was July 20th until 2003, not a holiday before 1996,
            # July 23rd in 2020 due to Olympics games
            # July 22nd in 2021 due to Olympics games
            or (weekday == Weekday.Monday and (15 <= day <= 21) and month == 7
                and ((2003 <= year < 2020) or year >= 2022))
            or ((day == 20 or (day == 21 and weekday == Weekday.Monday)) and month == 7
                and 1996 <= year < 2003)
            or (day == 23 and month == 7 and year == 2020)
            or (day == 22 and month == 7 and year == 2021)
            # Mountain Day
            # (moved in 2020 due to Olympics games)
            # (moved in 2021 due to Olympics games)
            or ((day == 11 or (day == 12 and weekday == Weekday.Monday)) and month == 8
                and ((2016 <= year < 2020) or year >= 2022))
            or (day == 10 and month == 8 and year == 2020)
            or (day == 9 and month == 8 and year == 2021)
            # Respect for the Aged Day (3rd Monday in September),
            # was September 15th until 2003
            or (weekday == Weekday.Monday and (15 <= day <= 21) and month == 9
                and year >= 2003)
            or ((day == 15 or (day == 16 and weekday == Weekday.Monday)) and month == 9
                and year < 2003)
            # If a single day falls between Respect for the Aged Day
            # and the Autumnal Equinox, it is holiday
            or (weekday == Weekday.Tuesday and day + 1 == ae and 16 <= day <= 22
                and month == 9 and year >= 2003)
            # Autumnal Equinox
            or ((day == ae or (day == ae + 1 and weekday == Weekday.Monday)) and month == 9)
            # Health and Sports Day (2nd Monday in October),
            # was October 10th until 2000,
            # July 24th in 2020 due to Olympics games
            # July 23rd in 2021 due to Olympics games
            or (weekday == Weekday.Monday and (8 <= day <= 14) and month == 10
                and ((2000 <= year < 2020) or year >= 2022))
            or ((day == 10 or (day == 11 and weekday == Weekday.Monday)) and month == 10
                and year < 2000)
            or (day == 24 and month == 7 and year == 2020)
            or (day == 23 and month == 7 and year == 2021)
            # National Culture Day
            or ((day == 3 or (day == 4 and weekday == Weekday.Monday)) and month == 11)
            # Labor Thanksgiving Day
            or ((day == 23 or (day == 24 and weekday == Weekday.Monday)) and month == 11)
            # Bank Holiday
            or (day == 31 and month == 12)
            # one-shot holidays
            # Marriage of Prince Akihito
            or (day == 10 and month == 4 and year == 1959)
            # Rites of Imperial Funeral
            or (day == 24 and month == 2 and year == 1989)
            # Enthronement Ceremony (Emperor Akihito)
            or (day == 12 and month == 11 and year == 1990)
            # Marriage of Prince Naruhito
            or (day == 9 and month == 6 and year == 1993)
            # Special holiday based on Japanese public holidays law
            or (day == 30 and month == 4 and year == 2019)
            # Enthronement Day (Emperor Naruhito)
            or (day == 1 and month == 5 and year == 2019)
            # Special holiday based on Japanese public holidays law
            or (day == 2 and month == 5 and year == 2019)
            # Enthronement Ceremony (Emperor Naruhito)
                or (day == 22 and month == 10 and year == 2019)):
            return False  # NOLINT(readability-simplify-boolean-expr)
        return True
