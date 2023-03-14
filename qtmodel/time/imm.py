from datetime import datetime, timedelta
from enum import Enum

from qtmodel.error import qt_require, QTError
from qtmodel.settings import Settings
from qtmodel.time.date import DateTool
from qtmodel.time.weekday import Weekday


class IMMMonth(Enum):
    """ Main cycle of the International %Money Market (a.k.a. %IMM) months """
    F = 1
    G = 2
    H = 3
    J = 4
    K = 5
    M = 6
    N = 7
    Q = 8
    U = 9
    V = 10
    X = 11
    Z = 12


class IMM:

    @staticmethod
    def is_imm_date(date: datetime, main_cycle: bool = True):
        """
        returns whether or not the given date is an IMM date
        :param date:
        :param main_cycle:
        :return:
        """
        if DateTool.weekday(date=date) != Weekday.Wednesday:
            return False

        day = date.day
        if day < 15 or day > 21:
            return False

        if not main_cycle:
            return True

        month = date.month
        if month == 3 or month == 6 or month == 9 or month == 12:
            return True
        else:
            return False

    @staticmethod
    def is_imm_code(in_str: str, main_cycle: bool = True):
        """
        returns whether or not the given string is an IMM code
        :param in_str:
        :param main_cycle:
        """
        if len(in_str) != 2:
            return False

        str1 = "0123456789"
        loc = str1.find(in_str[1])
        if loc == -1:
            return False

        if main_cycle:
            str1 = "hmzuHMZU"
        else:
            str1 = "fghjkmnquvxzFGHJKMNQUVXZ"
        loc = str1.find(in_str[0])
        return loc != -1


    @staticmethod
    def code(date: datetime):
        """
        returns the IMM code for the given date (e.g. H3 for March 20th, 2013).
        :param date:
        """
        qt_require(IMM.is_imm_date(date=date, main_cycle=False), f"{date} is not an IMM date")
        year = int(date.year % 10)
        month = date.month

        if month == 1:
            imm_code = 'F' + str(year)
        elif month == 2:
            imm_code = 'G' + str(year)
        elif month == 3:
            imm_code = 'H' + str(year)
        elif month == 4:
            imm_code = 'J' + str(year)
        elif month == 5:
            imm_code = 'K' + str(year)
        elif month == 6:
            imm_code = 'M' + str(year)
        elif month == 7:
            imm_code = 'N' + str(year)
        elif month == 8:
            imm_code = 'Q' + str(year)
        elif month == 9:
            imm_code = 'U' + str(year)
        elif month == 10:
            imm_code = 'V' + str(year)
        elif month == 11:
            imm_code = 'X' + str(year)
        elif month == 12:
            imm_code = 'Z' + str(year)
        else:
            raise QTError("not an IMM month (and it should have been)")
        return imm_code

    @staticmethod
    def date(imm_code: str, ref_date: datetime = None):
        """
        returns the IMM date for the given IMM code (e.g. March 20th, 2013 for H3).
        :param imm_code:
        :param ref_date:
        """
        qt_require(IMM.is_imm_code(in_str=imm_code, main_cycle=False), f"{imm_code} is not a valid IMM code")
        reference_date = ref_date if ref_date is not None else Settings().evaluation_date
        code = imm_code.upper()
        month_str = code[0]
        if month_str == "F":
            month = 1
        elif month_str == "G":
            month = 2
        elif month_str == "H":
            month = 3
        elif month_str == "J":
            month = 4
        elif month_str == "K":
            month = 5
        elif month_str == "M":
            month = 6
        elif month_str == "N":
            month = 7
        elif month_str == "Q":
            month = 8
        elif month_str == "U":
            month = 9
        elif month_str == "V":
            month = 10
        elif month_str == "X":
            month = 11
        elif month_str == "Z":
            month = 12
        else:
            raise QTError("invalid IMM month letter")

        year = int(code[1])
        # year<1900 are not valid QuantLib years: to avoid a run-time
        # exception few lines below we need to add 10 years right away
        if year == 0 and reference_date.year <= 1909:
            year += 10
        reference_year = reference_date.year % 10
        year += reference_date.year - reference_year
        result = IMM.next_date(date=datetime(year, month, 1), main_cycle=False)
        if result < reference_date:
            return IMM.next_date(date=datetime(year+10, month, 1), main_cycle=False)

        return result

    @staticmethod
    def next_date(date: datetime = None,
                  main_cycle: bool = True,
                  imm_code: str = None,
                  reference_date: datetime = None):
        """
        returns the 1st delivery date for next contract listed in the
        International Money Market section of the Chicago Mercantile
        Exchange.
        :param date:
        :param main_cycle:
        :param imm_code:
        :param reference_date:
        :return:
        """
        # next IMM date following the given IMM code
        if imm_code is not None:
            imm_date = IMM.date(imm_code=imm_code, ref_date=reference_date)
            one_day = timedelta(days=1)
            return IMM.next_date(date=imm_date+one_day, main_cycle=main_cycle)
        # next IMM date following the given date
        else:
            ref_date = Settings().evaluation_date if date is None else date
            year = ref_date.year
            month = ref_date.month
            offset = 3 if main_cycle else 1
            skip_months = offset - (month % offset)
            if skip_months != offset or ref_date.day > 21:
                skip_months += month
                if skip_months <= 12:
                    month = skip_months
                else:
                    month = skip_months - 12
                    year += 1

            result = DateTool.nth_weekday(nth=3, weekday=Weekday.Wednesday, year=year, month=month)
            if result <= ref_date:
                result = IMM.next_date(date=datetime(year, month, 22), main_cycle=main_cycle)
            return result

    @staticmethod
    def next_code(date: datetime = None,
                  main_cycle: bool = True,
                  imm_code: str = None,
                  reference_date: datetime = None):
        """
        returns the IMM code for next contract listed in the
        International Money Market section of the Chicago Mercantile
        Exchange.
        :param date:
        :param main_cycle:
        :param imm_code:
        :param reference_date:
        :return:
        """
        date = IMM.next_date(date=date,
                             main_cycle=main_cycle,
                             imm_code=imm_code,
                             reference_date=reference_date)
        return IMM.code(date=date)
