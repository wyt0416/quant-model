from qtmodel.exercise import Exercise
from qtmodel.instruments.payoffs import StrikedTypePayoff
from qtmodel.instruments.vanillaoption import VanillaOption


class EuropeanOption(VanillaOption):
    """ European option on a single asset """

    def __init__(self, payoff: StrikedTypePayoff, exercise: Exercise):
        super(EuropeanOption, self).__init__(payoff=payoff, exercise=exercise)
