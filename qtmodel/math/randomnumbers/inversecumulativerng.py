

class InverseCumulativeRng:
    """
    Inverse cumulative random number generator
    It uses a uniform deviate in (0, 1) as the source of cumulative
    distribution values.
    Then an inverse cumulative distribution is used to calculate
    the distribution deviate.

    The uniform deviate is supplied by RNG.
    """

    def __init__(self, ug):
        self._uniform_generator = ug

    def next(self):

