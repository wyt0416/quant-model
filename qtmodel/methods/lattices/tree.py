from qtmodel.patterns.curiouslyrecurring import CuriouslyRecurringTemplate


class Tree(CuriouslyRecurringTemplate):
    """ Tree approximating a single-factor diffusion """

    def __init__(self, columns: int):
        self._columns = columns

    def columns(self):
        return self._columns
