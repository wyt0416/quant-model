

class Extrapolator:
    """ base class for classes possibly allowing extrapolation """

    def __init__(self):
        self._extrapolate = False

    def enable_extrapolation(self, b: bool = True):
        """enable extrapolation in subsequent calls"""
        self._extrapolate = b

    def disable_extrapolation(self, b: bool = True):
        """disable extrapolation in subsequent calls"""
        self._extrapolate = not b

    def allows_extrapolation(self):
        """tells whether extrapolation is enabled"""
        return self._extrapolate

