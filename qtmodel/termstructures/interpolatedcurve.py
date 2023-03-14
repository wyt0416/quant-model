from datetime import datetime
from typing import List

from qtmodel.error import QTError
from qtmodel.math.interpolation import Interpolation
from qtmodel.types import Real


class InterpolatedCurve:
    """
    Helper class to build interpolated term structures
    Interpolated term structures can use proected or private
    inheritance from this class to obtain the relevant data
    members and implement correct copy behavior.
    """

    def __init__(self,
                 class_type,
                 times: List[Real] = None,
                 data: List[Real] = None,
                 n: int = None,
                 interpolator=None):
        if interpolator is None:
            interpolator = class_type()
        self._interpolator = interpolator
        if isinstance(times, list) and isinstance(data, list):
            self._times = times
            self._data = data
        elif isinstance(times, list):
            self._times = times
            self._data = [None] * len(times)
        elif isinstance(n, int):
            self._times = [None] * n
            self._data = [None] * n
        else:
            raise QTError("it's not in the four scenarios")

        self._interpolation: Interpolation = None
        # Usually, the maximum date is the one corresponding to the
        # last node. However, it might happen that a bit of
        # extrapolation is used by construction; for instance, when a
        # curve is bootstrapped and the last relevant date for an
        # instrument is after the corresponding pillar.
        # We provide here a slot to store this information, so that
        # it's available to all derived classes (we should have
        # probably done the same with the dates_ vector, but moving
        # it here might not be entirely backwards-compatible).
        self._max_date: datetime = None

    def setup_interpolation(self):
        self._interpolation = self._interpolator.interpolate(self._times,
                                                             self._data)
