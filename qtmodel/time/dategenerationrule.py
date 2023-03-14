from enum import Enum


class DateGenerationTypes(Enum):
    # Backward from termination date to effective date.
    Backward = "Backward"
    # Forward from effective date to termination date.
    Forward = "Forward"
    # No intermediate dates between effective date and termination date.
    Zero = "Zero"
    # All dates but effective date and termination date are taken to be
    # on the third wednesday of their month (with forward calculation.)
    Third_Wednesday = "Third Wednesday"
    # All dates including effective date and termination date are taken
    # to be on the third wednesday of their month (with forward calculation.)
    Third_Wednesday_Inclusive = "Third Wednesday Inclusive"
    # All dates but the effective date are taken to be the twentieth of
    # their month (used for CDS schedules in emerging markets.)
    # The termination date is also modified.
    Twentieth = "Twentieth"
    # All dates but the effective date are taken to be the twentieth of
    # an IMM month (used for CDS schedules.)
    # The termination date is also modified.
    Twentieth_IMM = "Twentieth IMM"
    # Same as TwentiethIMM with unrestricted date ends and log/short stub
    # coupon period (old CDS convention).
    Old_CDS = "Old CDS"
    # Credit derivatives standard rule since 'Big Bang' changes in 2009.
    CDS = "CDS"
    # Credit derivatives standard rule since December 20 th, 2015.
    CDS2015 = "CDS2015"
