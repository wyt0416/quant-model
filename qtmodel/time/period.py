from qtmodel.error import QTError
from qtmodel.time.frequency import Frequency
from qtmodel.time.timeunit import TimeUnit


class Period:
    def __init__(self,
                 n: int = None,
                 units: TimeUnit = None,
                 f: Frequency = None):
        """
        n and units should be inputted simultaneously, while f need to be inputted instead if n and units are missing
        :param n: length of time
        :param units: units of time
        :param f: frequency
        """
        if n is not None and units is not None:
            self.length = n
            self.units = units
        elif f is not None:
            self.freq = f
            if f == Frequency.NoFrequency:
                self.length = 0
                self.units = TimeUnit.Days
            elif f == Frequency.Once:
                self.length = 0
                self.units = TimeUnit.Years
            elif f == Frequency.Annual:
                self.length = 1
                self.units = TimeUnit.Years
            elif f == Frequency.Semiannual or \
                    f == Frequency.EveryFourthMonth or \
                    f == Frequency.Quarterly or \
                    f == Frequency.Bimonthly or \
                    f == Frequency.Monthly:
                self.length = 12 / f.value
                self.units = TimeUnit.Months
            elif f == Frequency.EveryFourthWeek or \
                    f == Frequency.Biweekly or \
                    f == Frequency.Weekly:
                self.length = 52 / f.value
                self.units = TimeUnit.Weeks
            elif f == Frequency.Daily:
                self.length = 1
                self.units = TimeUnit.Days
            else:
                raise QTError(f"unknown frequency ({f.value})")
        else:
            raise QTError("n and units must be passed together. If n and units are not passed, F must be passed")
        self.length = int(self.length)

    def frequency(self):
        """
        :return: Frequency
        """
        freq = getattr(self, 'freq', None)
        if freq is not None:
            return freq
        length = self.length
        units = self.units

        if length == 0:
            if units == TimeUnit.Years:
                return Frequency.Once
            else:
                return Frequency.NoFrequency
        if units == TimeUnit.Years:
            if length == 1:
                return Frequency.Annual
            else:
                return Frequency.OtherFrequency
        elif units == TimeUnit.Months:
            if 12 % length == 0 and length <= 12:
                return Frequency(12 / length)
            else:
                return Frequency.OtherFrequency
        elif units == TimeUnit.Weeks:
            if length == 1:
                return Frequency.Weekly
            elif length == 2:
                return Frequency.Biweekly
            elif length == 4:
                return Frequency.EveryFourthWeek
            else:
                return Frequency.OtherFrequency
        elif units == TimeUnit.Days:
            if length == 1:
                return Frequency.Daily
            else:
                return Frequency.OtherFrequency
        else:
            raise QTError(f"unknown time unit ({units.value})")

    def normalize(self):
        """
        :return: None
        """
        length = self.length
        units = self.units
        if length == 0:
            self.units = TimeUnit.Days
        else:
            if units == TimeUnit.Months:
                if length % 12 == 0:
                    self.length /= 12
                    self.units = TimeUnit.Years
                return
            elif units == TimeUnit.Days:
                if length % 7 == 0:
                    self.length /= 7
                    self.units = TimeUnit.Weeks
            elif units == TimeUnit.Weeks or \
                    units == TimeUnit.Years:
                return
            else:
                raise QTError(f"unknown time unit ({units.value})")

    def normalized(self):
        """
        :return: Period
        """
        period = Period(n=self.length, units=self.units)
        period.normalize()
        return period

    def months(self):
        """
        :return: float
        """
        length = self.length
        units = self.units
        if length == 0:
            return 0.0
        if units == TimeUnit.Days:
            raise QTError("cannot convert Days into Months")
        elif units == TimeUnit.Weeks:
            raise QTError("cannot convert Weeks into Months")
        elif units == TimeUnit.Months:
            return length
        elif units == TimeUnit.Years:
            return length * 12.0
        else:
            raise QTError(f"unknown time unit ({units.value})")

    def weeks(self):
        """
        :return: float
        """
        length = self.length
        units = self.units
        if length == 0:
            return 0.0
        if units == TimeUnit.Days:
            return length / 7.0
        elif units == TimeUnit.Weeks:
            return length
        elif units == TimeUnit.Months:
            raise QTError("cannot convert Months into Weeks")
        elif units == TimeUnit.Years:
            raise QTError("cannot convert Years into Weeks")
        else:
            raise QTError(f"unknown time unit ({units.value})")

    def days(self):
        """
        :return: float
        """
        length = self.length
        units = self.units
        if length == 0:
            return 0.0
        if units == TimeUnit.Days:
            return length
        elif units == TimeUnit.Weeks:
            return length * 7.0
        elif units == TimeUnit.Months:
            raise QTError("cannot convert Months into Days")
        elif units == TimeUnit.Years:
            raise QTError("cannot convert Years into Days")
        else:
            raise QTError(f"unknown time unit ({units.value})")

    @staticmethod
    def days_min_max(period):
        """
        :param period: Period
        :return:
        """
        length = period.length
        units = period.units
        if units == TimeUnit.Days:
            days_min = length
            days_max = length
        elif units == TimeUnit.Weeks:
            days_min = 7 * length
            days_max = 7 * length
        elif units == TimeUnit.Months:
            days_min = 28 * length
            days_max = 31 * length
        elif units == TimeUnit.Years:
            days_min = 365 * length
            days_max = 366 * length
        else:
            raise QTError(f"unknown time unit ({units.value})")
        return days_min, days_max

    def __neg__(self):
        """
        -self
        :return: Period
        """
        return Period(n=-self.length, units=self.units)

    def __iadd__(self, other):
        """
        self+=other.
        :param other: Period
        :return: Period
        """
        length = self.length
        units = self.units
        other_length = other.length
        other_units = other.units
        if length == 0:
            length = other_length
            units = other_units
        elif units == other_units:
            # no conversion needed
            length += other_length
        else:
            if units == TimeUnit.Years:
                if other_units == TimeUnit.Months:
                    units = TimeUnit.Months
                    length = length * 12 + other_length
                elif other_units == TimeUnit.Weeks or other_units == TimeUnit.Days:
                    if other_length != 0:
                        raise QTError(f"impossible addition between {self} and {other}")
                else:
                    QTError(f"unknown time unit ({other_units.value})")
            elif units == TimeUnit.Months:
                if other_units == TimeUnit.Years:
                    length += other_length * 12
                elif other_units == TimeUnit.Weeks or other_units == TimeUnit.Days:
                    if other_length != 0:
                        raise QTError(f"impossible addition between {self} and {other}")
                else:
                    QTError(f"unknown time unit ({other_units.value})")
            elif units == TimeUnit.Weeks:
                if other_units == TimeUnit.Days:
                    units = TimeUnit.Days
                    length = length * 7 + other_length
                elif other_units == TimeUnit.Years or other_units == TimeUnit.Months:
                    if other_length != 0:
                        raise QTError(f"impossible addition between {self} and {other}")
                else:
                    QTError(f"unknown time unit ({other_units.value})")
            elif units == TimeUnit.Days:
                if other_units == TimeUnit.Weeks:
                    length += other_length * 7
                elif other_units == TimeUnit.Years or other_units == TimeUnit.Months:
                    if other_length != 0:
                        raise QTError(f"impossible addition between {self} and {other}")
                else:
                    QTError(f"unknown time unit ({other_units.value})")
            else:
                QTError(f"unknown time unit ({units.value})")
        self.length, self.units = length, units
        return self

    def __add__(self, other):
        """
        self+other.
        :param other: Period
        :return: Period
        """
        temp_period = Period(n=self.length, units=self.units)
        temp_period += other
        return temp_period

    def __isub__(self, other):
        """
        self-=other.
        :param other: Period
        :return: Period
        """
        self += (-other)
        return self

    def __sub__(self, other):
        """
        self-other.
        :param other: Period
        :return: Period
        """
        return self + (-other)

    def __itruediv__(self, n: int):
        """
        self/=n.
        :param n: int
        :return: Period
        """
        if n == 0:
            raise QTError("cannot be divided by zero")
        length = self.length
        units = self.units
        if length % n == 0:
            length = int(length / n)
        else:
            if units == TimeUnit.Years:
                length *= 12
                units = TimeUnit.Months
            elif units == TimeUnit.Weeks:
                length *= 7
                units = TimeUnit.Days
            else:
                pass
            if length % n != 0:
                raise QTError(f"{self} cannot be divided by {n}")
            length = int(length / n)
            units = units
        self.length, self.units = length, units
        return self

    def __truediv__(self, n: int):
        """
        self/n.
        :param n: int
        :return: Period
        """
        temp_period = Period(n=self.length, units=self.units)
        temp_period /= n
        return temp_period

    def __imul__(self, n: int):
        """
        self*=n.
        :param n: int
        :return: Period
        """
        self.length *= n
        return self

    def __mul__(self, n: int):
        """
        self*n.
        :param n: int
        :return: Period
        """
        temp_period = Period(n=self.length, units=self.units)
        temp_period *= n
        return temp_period

    def __rmul__(self, n: int):
        """
        n*self
        :param n: int
        :return:
        """
        return self * n

    def __eq__(self, other):
        """
        self==other.
        :param other: Period
        :return: bool
        """
        return not (self < other or other < self)

    def __ne__(self, other):
        """
        self!=other.
        :param other: Period
        :return: bool
        """
        return not (self == other)

    def __lt__(self, other):
        """
        self<other.
        :param other: Period
        :return: bool
        """
        length = self.length
        units = self.units
        other_length = other.length
        other_units = other.units
        # special cases
        if length == 0:
            return other_length > 0
        if other_length == 0:
            return length < 0

        # exact comparisons
        if units == other_units:
            return length < other_length
        if units == TimeUnit.Months and other_units == TimeUnit.Years:
            return length < 12 * other_length
        if units == TimeUnit.Years and other_units == TimeUnit.Months:
            return 12 * length < other_length
        if units == TimeUnit.Days and other_units == TimeUnit.Weeks:
            return length < 7 * other_length
        if units == TimeUnit.Weeks and other_units == TimeUnit.Days:
            return 7 * length < other_length

        days_min, days_max = Period.days_min_max(self)
        other_days_min, other_days_max = Period.days_min_max(other)
        if days_max < other_days_min:
            return True
        elif days_min > other_days_max:
            return False
        else:
            raise QTError(f"undecidable comparison between {self} and {other}")

    def __gt__(self, other):
        """
        self>other.
        :param other: Period
        :return: bool
        """
        return other < self

    def __le__(self, other):
        """
        self<=other.
        :param other: Period
        :return: bool
        """
        return not (self > other)

    def __ge__(self, other):
        """
        self>=other.
        :param other: Period
        :return: bool
        """
        return not (self < other)

    def __repr__(self):
        return f'{self.length}{self.units.name}'
