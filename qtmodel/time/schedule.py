import bisect
import copy
from datetime import datetime, timedelta
from typing import List

from qtmodel.error import QTError, qt_require, qt_ensure
from qtmodel.settings import Settings
from qtmodel.time.businessdayconvention import BusinessDayConvention
from qtmodel.time.calendar import Calendar
from qtmodel.time.calendars.nullcalendar import NullCalendar
from qtmodel.time.date import DateTool
from qtmodel.time.dategenerationrule import DateGenerationTypes
from qtmodel.time.frequency import Frequency
from qtmodel.time.imm import IMM
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit
from qtmodel.time.weekday import Weekday


class Schedule:

    def __init__(self,
                 effective_date: datetime = None,
                 termination_date: datetime = None,
                 tenor: Period = None,
                 calendar: Calendar = NullCalendar(),
                 convention: BusinessDayConvention = BusinessDayConvention.Unadjusted,
                 termination_date_convention: BusinessDayConvention = None,
                 rule: DateGenerationTypes = None,
                 end_of_month: bool = None,
                 first_date: datetime = None,
                 next_to_last_date: datetime = None,
                 dates: List[datetime] = None,
                 is_regular: List[bool] = None):
        self.tenor_ = tenor
        self.calendar = calendar
        self.convention = convention
        self.termination_date_convention_ = termination_date_convention
        self.rule_ = rule
        if dates is not None:
            self.dates = dates
            self.is_regular_ = is_regular
            if tenor is not None and not Schedule.allows_end_of_month(tenor=tenor):
                self.end_of_month_ = False
            else:
                self.end_of_month_ = end_of_month

            qt_require(
                self.is_regular_ is None or (self.is_regular_ is not None and len(self.is_regular_) == len(dates) - 1),
                "is_regular length must be zero or equal to the number of dates minus 1")
        elif termination_date is not None:
            self.effective_date = effective_date
            self.termination_date = termination_date
            self.end_of_month_ = end_of_month if Schedule.allows_end_of_month(tenor) else False
            self.first_date = None if first_date == self.effective_date else first_date
            self.next_to_last_date = None if next_to_last_date == termination_date else next_to_last_date
            self.dates = []
            self.is_regular_ = []

            # in many cases (e.g. non-expired bonds) the effective date is not really necessary.
            # In these cases a decent placeholder is enough
            if self.effective_date is None and first_date is None and rule == DateGenerationTypes.Backward:
                eval_date = Settings().evaluation_date
                qt_require(eval_date < termination_date, "null effective date")
                if next_to_last_date is not None:
                    year = int((next_to_last_date - eval_date).days / 366 + 1)
                    self.effective_date = DateTool.advance(date=next_to_last_date, n=-year, units=TimeUnit.Years)
                else:
                    year = int((termination_date - eval_date).days / 366 + 1)
                    self.effective_date = DateTool.advance(date=termination_date, n=-year, units=TimeUnit.Years)
            else:
                qt_require(self.effective_date is not None, "null effective date")

            qt_require(self.effective_date < termination_date,
                       f"effective date ({self.effective_date}) later than or equal to termination date ({termination_date})")

            if tenor.length == 0:
                self.rule_ = DateGenerationTypes.Zero
            else:
                qt_require(tenor.length > 0, f"non positive tenor ({tenor}) not allowed")

            if self.first_date is not None:
                if self.rule_ == DateGenerationTypes.Backward or self.rule_ == DateGenerationTypes.Forward:
                    qt_require(self.effective_date < self.first_date <= termination_date,
                               f"first date ({self.first_date}) out of effective-termination date range ({self.effective_date}, {termination_date}]")
                elif self.rule_ == DateGenerationTypes.Third_Wednesday:
                    qt_require(IMM.is_imm_date(date=self.first_date, main_cycle=False),
                               f"first date ({self.first_date}) is not an IMM date")
                elif self.rule_ == DateGenerationTypes.Zero or \
                        self.rule_ == DateGenerationTypes.Twentieth or \
                        self.rule_ == DateGenerationTypes.Twentieth_IMM or \
                        self.rule_ == DateGenerationTypes.Old_CDS or \
                        self.rule_ == DateGenerationTypes.CDS or \
                        self.rule_ == DateGenerationTypes.CDS2015:
                    raise QTError(f"first date incompatible with {self.rule_} date generation rule")
                else:
                    raise QTError(f"unknown rule ({self.rule_}))")

            if self.next_to_last_date is not None:
                if self.rule_ == DateGenerationTypes.Backward or \
                        self.rule_ == DateGenerationTypes.Forward:
                    qt_require(self.effective_date <= self.next_to_last_date < termination_date,
                               f"next to last date ({self.next_to_last_date}) out of effective-termination date range [{self.effective_date}, {termination_date})")
                elif self.rule_ == DateGenerationTypes.Third_Wednesday:
                    qt_require(IMM.is_imm_date(date=self.next_to_last_date, main_cycle=False),
                               f"next-to-last date ({self.next_to_last_date}) is not an IMM date")
                elif self.rule_ == DateGenerationTypes.Zero or \
                        self.rule_ == DateGenerationTypes.Twentieth or \
                        self.rule_ == DateGenerationTypes.Twentieth_IMM or \
                        self.rule_ == DateGenerationTypes.Old_CDS or \
                        self.rule_ == DateGenerationTypes.CDS or \
                        self.rule_ == DateGenerationTypes.CDS2015:
                    raise QTError(f"next to last date incompatible with {self.rule_} date generation rule")
                else:
                    raise QTError(f"unknown rule ({self.rule_})")

            # calendar needed for endOfMonth adjustment
            self.null_calendar = NullCalendar()
            self.periods = 1
            self.seed = None
            exit_date = None
            if self.rule_ == DateGenerationTypes.Zero:
                self.tenor_ = Period(n=0, units=TimeUnit.Years)
                self.dates.append(self.effective_date)
                self.dates.append(termination_date)
                self.is_regular_.append(True)
            elif self.rule_ == DateGenerationTypes.Backward:
                self.dates.append(termination_date)
                self.seed = termination_date
                if self.next_to_last_date is not None:
                    self.dates.insert(0, self.next_to_last_date)
                    temp = self.null_calendar.advance(date=self.seed, period=-self.periods * self.tenor_,
                                                      convention=convention,
                                                      end_of_month=self.end_of_month_)
                    if temp != self.next_to_last_date:
                        self.is_regular_.insert(0, False)
                    else:
                        self.is_regular_.insert(0, True)
                    self.seed = self.next_to_last_date

                exit_date = self.effective_date
                if self.first_date is not None:
                    exit_date = self.first_date

                while 1:
                    temp = self.null_calendar.advance(date=self.seed, period=-self.periods * self.tenor_,
                                                      convention=convention,
                                                      end_of_month=self.end_of_month_)
                    if temp < exit_date:
                        if self.first_date is not None and \
                                (self.calendar.adjust(self.dates[0], convention) !=
                                 self.calendar.adjust(self.first_date, convention)):
                            self.dates.insert(0, self.first_date)
                            self.is_regular_.insert(0, False)
                        break
                    else:
                        # skip dates that would result in duplicates after adjustment
                        if self.calendar.adjust(self.dates[0], convention) != self.calendar.adjust(temp, convention):
                            self.dates.insert(0, temp)
                            self.is_regular_.insert(0, True)
                        self.periods += 1

                if self.calendar.adjust(self.dates[0], convention) != self.calendar.adjust(self.effective_date,
                                                                                           convention):
                    self.dates.insert(0, self.effective_date)
                    self.is_regular_.insert(0, False)
            elif self.rule_ == DateGenerationTypes.Twentieth or \
                    self.rule_ == DateGenerationTypes.Twentieth_IMM or \
                    self.rule_ == DateGenerationTypes.Third_Wednesday or \
                    self.rule_ == DateGenerationTypes.Third_Wednesday_Inclusive or \
                    self.rule_ == DateGenerationTypes.Old_CDS or \
                    self.rule_ == DateGenerationTypes.CDS or \
                    self.rule_ == DateGenerationTypes.CDS2015:
                qt_require(not self.end_of_month_,
                           f"end_of_month convention incompatible with {self.rule_} date generation rule")
                self._init_attr()
            elif self.rule_ == DateGenerationTypes.Forward:
                self._init_attr()
            else:
                raise QTError(f"unknown rule ({self.rule_})")

            # adjustments
            if self.rule_ == DateGenerationTypes.Third_Wednesday:
                i = 1
                length = len(self.dates)
                while i < length - 1:
                    self.dates[i] = DateTool.nth_weekday(nth=3, weekday=Weekday.Wednesday, year=self.dates[i].year,
                                                         month=self.dates[i].month)
                    i += 1
            elif self.rule_ == DateGenerationTypes.Third_Wednesday_Inclusive:
                for i in range(len(self.dates)):
                    self.dates[i] = DateTool.nth_weekday(nth=3, weekday=Weekday.Wednesday, year=self.dates[i].year,
                                                         month=self.dates[i].month)

            if self.end_of_month_ and self.calendar.is_end_of_month(date=self.seed):
                # adjust to end of month
                if convention == BusinessDayConvention.Unadjusted:
                    i = 1
                    length = len(self.dates)
                    while i < length - 1:
                        self.dates[i] = DateTool.end_of_month(date=self.dates[i])
                        i += 1
                else:
                    i = 1
                    length = len(self.dates)
                    while i < length - 1:
                        self.dates[i] = self.calendar.end_of_month(date=self.dates[i])
                        i += 1
                d1 = self.dates[0]
                d2 = self.dates[-1]
                if termination_date_convention != BusinessDayConvention.Unadjusted:
                    d1 = self.calendar.end_of_month(date=self.dates[0])
                    d2 = self.calendar.end_of_month(date=self.dates[-1])
                else:
                    # the termination date is the first if going backwards, the last otherwise.
                    if self.rule_ == DateGenerationTypes.Backward:
                        d2 = DateTool.end_of_month(date=self.dates[-1])
                    else:
                        d1 = DateTool.end_of_month(date=self.dates[0])
                # if the eom adjustment leads to a single date schedule we do not apply it
                if d1 != d2:
                    self.dates[0] = d1
                    self.dates[-1] = d2
            else:
                # first date not adjusted for old CDS schedules
                if self.rule_ != DateGenerationTypes.Old_CDS:
                    self.dates[0] = self.calendar.adjust(date=self.dates[0], convention=self.convention)
                i = 1
                length = len(self.dates)
                while i < length - 1:
                    self.dates[i] = self.calendar.adjust(date=self.dates[i], convention=self.convention)
                    i += 1
                # termination date is NOT adjusted as per ISDA specifications,
                # unless otherwise specified in the confirmation of the deal or
                # unless we're creating a CDS schedule
                if termination_date_convention != BusinessDayConvention.Unadjusted and \
                        self.rule_ != DateGenerationTypes.CDS and \
                        self.rule_ != DateGenerationTypes.CDS2015:
                    self.dates[-1] = self.calendar.adjust(date=self.dates[-1], convention=termination_date_convention)

            # Final safety checks to remove extra next-to-last date,
            # if necessary.  It can happen to be equal or later than
            # the end date due to EOM adjustments (see the Schedule
            # test suite for an example).
            length = len(self.dates)
            if length >= 2 and self.dates[length - 2] >= self.dates[-1]:
                # there might be two dates only, then isRegular_ has size one
                is_regular_length = len(self.is_regular_)
                if is_regular_length >= 2:
                    self.is_regular_[is_regular_length - 2] = (self.dates[length - 2] == self.dates[-1])
                self.dates[length - 2] = self.dates[-1]
                self.dates.pop()
                self.is_regular_.pop()
            if length >= 2 and self.dates[1] <= self.dates[0]:
                self.is_regular_[1] = (self.dates[1] == self.dates[0])
                self.dates[1] = self.dates[0]
                self.dates.pop(0)
                self.is_regular_.pop(0)

            qt_ensure(length > 1, f'''degenerate single date ({self.dates[0]}) schedule
            self.seed date: {self.seed}
            exit date: {exit_date}
            effective date: " {self.effective_date}
            first date: " {self.first_date}
            next to last date: " {self.next_to_last_date}
            termination date: " {self.termination_date}
            generation rule: " {self.rule_}
            end of month: " {self.end_of_month_}''')
        else:
            raise QTError("the initialization parameters are incorrect")

    def _init_attr(self):
        if self.rule_ == DateGenerationTypes.CDS or \
                self.rule_ == DateGenerationTypes.CDS2015:
            prev_20th = self.previous_twentieth(date=self.effective_date, rule=self.rule_)
            if self.calendar.adjust(date=prev_20th, convention=self.convention) > self.effective_date:
                self.dates.append(DateTool.advance(date=prev_20th, n=-3, units=TimeUnit.Months))
                self.is_regular_.append(True)
            self.dates.append(prev_20th)
        else:
            self.dates.append(self.effective_date)

        self.seed = self.dates[-1]

        if self.first_date is not None:
            self.dates.append(self.first_date)
            temp = self.null_calendar.advance(date=self.seed, period=self.periods * self.tenor_, convention=self.convention,
                                              end_of_month=self.end_of_month_)
            if temp != self.first_date:
                self.is_regular_.append(False)
            else:
                self.is_regular_.append(True)
            self.seed = self.first_date
        elif self.rule_ == DateGenerationTypes.Twentieth or \
                self.rule_ == DateGenerationTypes.Twentieth_IMM or \
                self.rule_ == DateGenerationTypes.Old_CDS or \
                self.rule_ == DateGenerationTypes.CDS or \
                self.rule_ == DateGenerationTypes.CDS2015:
            next_20th = self.next_twentieth(date=self.effective_date, rule=self.rule_)
            if self.rule_ == DateGenerationTypes.Old_CDS:
                # distance rule inforced in natural days
                stub_days = 30
                if (next_20th - self.effective_date).days < stub_days:
                    # +1 will skip this one and get the next
                    next_20th = self.next_twentieth(date=next_20th + timedelta(days=1), rule=self.rule_)
            if next_20th != self.effective_date:
                self.dates.append(next_20th)
                self.is_regular_.append(
                    self.rule_ == DateGenerationTypes.CDS or self.rule_ == DateGenerationTypes.CDS2015)
                self.seed = next_20th

        exit_date = self.termination_date
        if self.next_to_last_date is not None:
            exit_date = self.next_to_last_date
        while 1:
            temp = self.null_calendar.advance(date=self.seed, period=self.periods * self.tenor_, convention=self.convention,
                                              end_of_month=self.end_of_month_)
            if temp > exit_date:
                if self.next_to_last_date is not None and \
                        (self.calendar.adjust(date=self.dates[-1], convention=self.convention) !=
                         self.calendar.adjust(date=self.next_to_last_date, convention=self.convention)):
                    self.dates.append(self.next_to_last_date)
                    self.is_regular_.append(False)
                break
            else:
                # skip dates that would result in duplicates after adjustment
                if self.calendar.adjust(date=self.dates[-1], convention=self.convention) != self.calendar.adjust(
                        date=temp, convention=self.convention):
                    self.dates.append(temp)
                    self.is_regular_.append(True)
                self.periods += 1

        if self.calendar.adjust(date=self.dates[-1],
                                convention=self.termination_date_convention_) != self.calendar.adjust(
            date=self.termination_date, convention=self.termination_date_convention_):
            if self.rule_ == DateGenerationTypes.Twentieth or \
                    self.rule_ == DateGenerationTypes.Twentieth_IMM or \
                    self.rule_ == DateGenerationTypes.Old_CDS or \
                    self.rule_ == DateGenerationTypes.CDS or \
                    self.rule_ == DateGenerationTypes.CDS2015:
                self.dates.append(self.next_twentieth(date=self.termination_date, rule=self.rule_))
                self.is_regular_.append(True)
            else:
                self.dates.append(self.termination_date)
                self.is_regular_.append(False)

    @staticmethod
    def next_twentieth(date: datetime, rule: DateGenerationTypes):
        result = datetime(date.year, date.month, 20)
        if result < date:
            result = DateTool.advance(date=result, n=1, units=TimeUnit.Months)
        if rule == DateGenerationTypes.Twentieth_IMM or \
                rule == DateGenerationTypes.Old_CDS or \
                rule == DateGenerationTypes.CDS or \
                rule == DateGenerationTypes.CDS2015:
            month = result.month
            if month % 3 != 0:
                # not a main IMM nmonth
                skip = 3 - month % 3
                result = DateTool.advance(date=result, n=skip, units=TimeUnit.Months)
        return result

    @staticmethod
    def allows_end_of_month(tenor: Period):
        return (tenor.units == TimeUnit.Months or tenor.units == TimeUnit.Years) and \
               tenor >= Period(n=1, units=TimeUnit.Months)

    @staticmethod
    def previous_twentieth(date: datetime, rule: DateGenerationTypes):
        result = datetime(date.year, date.month, 20)
        if result > date:
            result = DateTool.advance(date=result, n=-1, units=TimeUnit.Months)
        if rule == DateGenerationTypes.Twentieth_IMM or \
                rule == DateGenerationTypes.Old_CDS or \
                rule == DateGenerationTypes.CDS or \
                rule == DateGenerationTypes.CDS2015:
            month = result.month
            if month % 3 != 0:
                # not a main IMM nmonth
                skip = month % 3
                result = DateTool.advance(date=result, n=-skip, units=TimeUnit.Months)
        return result

    def after(self, truncation_date: datetime):
        result = copy.deepcopy(self)
        qt_require(truncation_date < result.dates[-1],
                   f"truncation date {truncation_date} must be before the last schedule date {result.dates[-1]}")
        if truncation_date > result.dates[0]:
            # remove earlier dates
            while result.dates[0] < truncation_date:
                result.dates.pop(0)
                if len(result.is_regular_):
                    result.is_regular_.pop(0)
            # add truncationDate if missing
            if truncation_date != result.dates[0]:
                result.dates.insert(0, truncation_date)
                result.is_regular_.insert(0, False)
                result.termination_date_convention_ = BusinessDayConvention.Unadjusted
            else:
                result.termination_date_convention_ = self.convention

            if result.next_to_last_date is not None and result.next_to_last_date <= truncation_date:
                result.next_to_last_date = None
            if result.first_date is not None and result.first_date <= truncation_date:
                result.first_date = None

        return result

    def until(self, truncation_date: datetime):
        result = copy.deepcopy(self)
        qt_require(truncation_date > result.dates[0],
                   f"truncation date {truncation_date} must be later than schedule first date {result.dates[0]}")
        if truncation_date < result.dates[-1]:
            # remove later dates
            while result.dates[-1] > truncation_date:
                result.dates.pop()
                if len(result.is_regular_):
                    result.is_regular_.pop()

            # add truncationDate if missing
            if truncation_date != result.dates[-1]:
                result.dates.append(truncation_date)
                result.is_regular_.append(False)
                result.termination_date_convention_ = BusinessDayConvention.Unadjusted
            else:
                result.termination_date_convention_ = self.convention

            if result.next_to_last_date is not None and result.next_to_last_date >= truncation_date:
                result.next_to_last_date = None
            if result.first_date is not None and result.first_date >= truncation_date:
                result.first_date = None

        return result

    def lower_bound_index(self, ref_date: datetime = None):
        d = Settings().evaluation_date if ref_date is None else ref_date
        index = bisect.bisect_left(self.dates, d)
        return index

    def lower_bound(self, ref_date: datetime = None):
        index = self.lower_bound_index(ref_date=ref_date)
        if index <= len(self.dates) - 1:
            return self.dates[index]
        else:
            return None

    def next_date(self, ref_date: datetime):
        res = self.lower_bound(ref_date=ref_date)
        return res

    def previous_date(self, ref_date: datetime):
        res_index = self.lower_bound_index(ref_date=ref_date)
        if res_index != 0:
            return self.dates[res_index - 1]
        else:
            return None

    def has_is_regular(self):
        return len(self.is_regular_) > 0

    def is_regular(self, i: int = None):
        qt_require(self.has_is_regular(), "full interface (is_regular) not available")
        if i is None:
            return self.is_regular_
        qt_require(len(self.is_regular_) >= i > 0,
                   f"index ({i}) must be in [1, {len(self.is_regular_)}]")
        return self.is_regular_[i - 1]

    def size(self):
        return len(self.dates)

    def empty(self):
        return len(self.dates) == 0

    def start_date(self):
        return self.dates[0]

    def end_date(self):
        return self.dates[-1]

    def has_tenor(self):
        return self.tenor_ is not None

    def tenor(self):
        qt_require(self.has_tenor(), "full interface (tenor) not available")
        return self.tenor_

    def has_termination_date_business_day_convention(self):
        return self.termination_date_convention_ is not None

    def termination_date_business_day_convention(self):
        qt_require(self.has_termination_date_business_day_convention(),
                   "full interface (termination date bdc) not available")
        return self.termination_date_convention_

    def has_rule(self):
        return self.rule_ is not None

    def rule(self):
        qt_require(self.has_rule(), "full interface (rule) not available")
        return self.rule_

    def has_end_of_month(self):
        return self.end_of_month_ is not None

    def end_of_month(self):
        qt_require(self.has_end_of_month(), "full interface (end of month) not available")
        return self.end_of_month_

    def __getitem__(self, item):
        return self.dates[item]


class MakeSchedule:
    """ helper class: This class provides a more comfortable interface
    to the argument list of Schedule's constructor. """

    def __init__(self):
        self._calendar = None
        self._effective_date = None
        self._termination_date = None
        self._tenor = None
        self._convention = None
        self._termination_date_convention = None
        self._rule = DateGenerationTypes.Backward
        self._end_of_month = None
        self._first_date = None
        self._next_to_last_date = None

    def begin(self, effective_date: datetime):
        self._effective_date = effective_date
        return self

    def end(self, termination_date: datetime):
        self._termination_date = termination_date
        return self

    def with_tenor(self, tenor: Period):
        self._tenor = tenor
        return self

    def with_frequency(self, frequency: Frequency):
        self._tenor = Period(f=frequency)
        return self

    def with_calendar(self, calendar: Calendar):
        self._calendar = calendar
        return self

    def with_convention(self, convention: BusinessDayConvention):
        self._convention = convention
        return self

    def with_termination_date_convention(self, convention: BusinessDayConvention):
        self._termination_date_convention = convention
        return self

    def with_rule(self, rule: DateGenerationTypes):
        self._rule = rule
        return self

    def forwards(self):
        self._rule = DateGenerationTypes.Forward
        return self

    def backwards(self):
        self._rule = DateGenerationTypes.Backward
        return self

    def end_of_month(self, flag: bool = True):
        self._end_of_month = flag
        return self

    def with_first_date(self, date: datetime):
        self._first_date = date
        return self

    def with_next_to_last_date(self, date: datetime):
        self._next_to_last_date = date
        return self

    def schedule(self):
        # check for mandatory arguments
        qt_require(self._effective_date is not None, "effective date not provided")
        qt_require(self._termination_date is not None, "termination date not provided")
        qt_require(self._tenor is not None, "tenor/frequency not provided")

        # if a convention was set, we use it.
        if self._convention is not None:
            convention = self._convention
        else:
            if self._calendar is not None:
                # if we set a calendar, we probably want it to be used
                convention = BusinessDayConvention.Following
            else:
                # if not, we don't care.
                convention = BusinessDayConvention.Unadjusted

        # if set explicitly, we use it;
        if self._termination_date_convention is not None:
            termination_date_convention = self._termination_date_convention
        else:
            # Unadjusted as per ISDA specification
            termination_date_convention = convention

        calendar = self._calendar
        if calendar is None:
            # we use a null one.
            calendar = NullCalendar()

        return Schedule(effective_date=self._effective_date,
                        termination_date=self._termination_date,
                        tenor=self._tenor,
                        calendar=calendar,
                        convention=convention,
                        termination_date_convention=termination_date_convention,
                        rule=self._rule,
                        end_of_month=self._end_of_month,
                        first_date=self._first_date,
                        next_to_last_date=self._next_to_last_date)
