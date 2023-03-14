from qtmodel.error import TestError
from qtmodel.time.period import Period
from qtmodel.time.timeunit import TimeUnit


def test_years_months_algebra():
    print("Testing period algebra on years/months...")

    one_year = Period(1, TimeUnit.Years)
    six_months = Period(6, TimeUnit.Months)
    three_months = Period(3, TimeUnit.Months)

    n = 4
    if one_year / n != three_months:
        raise TestError(f"division error: {one_year} / {n} not equal to {three_months}")

    n = 2
    if one_year / n != six_months:
        raise TestError(f"division error: {one_year} / {n} not equal to {six_months}")

    sum_ = three_months
    sum_ += six_months
    if sum_ != Period(9, TimeUnit.Months):
        raise TestError(f"sum error: {three_months} + {six_months} != {Period(9, TimeUnit.Months)}")

    sum_ += one_year
    if sum_ != Period(21, TimeUnit.Months):
        raise TestError(f"sum error: {three_months} + {six_months} + {one_year} != {Period(21, TimeUnit.Months)}")

    twelve_months = Period(12, TimeUnit.Months)
    if twelve_months.length != 12:
        raise TestError(
            f"normalization error: twelve_months.length() is {twelve_months.length} instead of 12")
    if twelve_months.units != TimeUnit.Months:
        raise TestError(
            f"normalization error: twelve_months.units() is {twelve_months.units} instead of {TimeUnit.Months}")

    normalized_twelve_months = Period(12, TimeUnit.Months)
    normalized_twelve_months.normalize()
    if normalized_twelve_months.length != 1:
        raise TestError(
            f"normalization error: normalized_twelve_months.length() is {normalized_twelve_months.length} instead of 1")
    if normalized_twelve_months.units != TimeUnit.Years:
        raise TestError(
            f"normalization error: normalized_twelve_months.units() is {normalized_twelve_months.units} instead of {TimeUnit.Years}")


def test_weeks_days_algebra():
    print("Testing period algebra on weeks/days...")

    two_weeks = Period(2, TimeUnit.Weeks)
    one_week = Period(1, TimeUnit.Weeks)
    three_days = Period(3, TimeUnit.Days)
    one_day = Period(1, TimeUnit.Days)

    n = 2
    if two_weeks / n != one_week:
        raise TestError(f"division error: {two_weeks} / {n} not equal to {one_week}")

    n = 7
    if one_week / n != one_day:
        raise TestError(f"division error: {one_week} / {n} not equal to {one_day}")

    sum_ = three_days
    sum_ += one_day
    if sum_ != Period(4, TimeUnit.Days):
        raise TestError(f"sum error: {three_days} + {one_day} != {Period(4, TimeUnit.Days)}")

    sum_ += one_week
    if sum_ != Period(11, TimeUnit.Days):
        raise TestError(f"sum error: {three_days} + {one_day} + {one_week} != {Period(11, TimeUnit.Days)}")

    seven_days = Period(7, TimeUnit.Days)
    if seven_days.length != 7:
        raise TestError(
            f"normalization error: seven_days.length() is {seven_days.length} instead of 7")
    if seven_days.units != TimeUnit.Days:
        raise TestError(
            f"normalization error: seven_days.units() is {seven_days.units} instead of {TimeUnit.Days}")


def test_normalization():
    print("Testing period normalization...")

    test_values = [
        Period(0, TimeUnit.Days),
        Period(0, TimeUnit.Weeks),
        Period(0, TimeUnit.Months),
        Period(0, TimeUnit.Years),
        Period(3, TimeUnit.Days),
        Period(7, TimeUnit.Days),
        Period(14, TimeUnit.Days),
        Period(30, TimeUnit.Days),
        Period(60, TimeUnit.Days),
        Period(365, TimeUnit.Days),
        Period(1, TimeUnit.Weeks),
        Period(2, TimeUnit.Weeks),
        Period(4, TimeUnit.Weeks),
        Period(8, TimeUnit.Weeks),
        Period(52, TimeUnit.Weeks),
        Period(1, TimeUnit.Months),
        Period(2, TimeUnit.Months),
        Period(6, TimeUnit.Months),
        Period(12, TimeUnit.Months),
        Period(18, TimeUnit.Months),
        Period(24, TimeUnit.Months),
        Period(1, TimeUnit.Years),
        Period(2, TimeUnit.Years)
    ]

    for period1 in test_values:
        normalized1 = period1.normalized()
        if normalized1 != period1:
            raise TestError(f"Normalizing {period1} yields {normalized1}, which compares different")

        for period2 in test_values:
            normalized2 = period2.normalized()
            try:
                comparison = (period1 == period2)
            except:
                pass

            if comparison:
                if normalized1.units != normalized2.units or normalized1.length != normalized2.length:
                    raise TestError(
                        f"{period1} and {period2} compare equal, but normalize to {normalized1} and {normalized2} respectively")

            if normalized1.units == normalized2.units and normalized1.length == normalized2.length:
                if period1 != period2:
                    raise TestError(
                        f"{period1} and {period2} compare different, but normalize to {normalized1} and {normalized2} respectively")
