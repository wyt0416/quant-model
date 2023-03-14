from qtmodel.types import Real


class Sample:
    """ weighted sample """

    def __init__(self, value, weight: Real):
        self.value = value
        self.weight = weight
