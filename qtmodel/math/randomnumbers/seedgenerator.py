import time

from qtmodel.math.randomnumbers.mt19937uniformrng import MersenneTwisterUniformRng
from qtmodel.patterns.singleton import SingletonType


class SeedGenerator(metaclass=SingletonType):
    """
    Random seed generator
    Random number generator used for automatic generation of
    initialization seeds.
    """

    def __init__(self):
        """ we need to prevent rng from being default-initialized """
        self._rng = MersenneTwisterUniformRng(seed=42)

    def get(self):
        return self._rng.next_int32()

    def initialize(self):
        # first_seed is chosen based on clock() and used for the first rng
        first_seed = int(time.time())
        first = MersenneTwisterUniformRng(seed=first_seed)

        # second_seed is as random as it could be
        # feel free to suggest improvements
        second_seed = first.next_int32()

        second = MersenneTwisterUniformRng(seed=second_seed)

        # use the second rng to initialize the final one
        skip = second.next_int32() % 1000
        init = [second.next_int32(), second.next_int32(), second.next_int32(), second.next_int32()]

        self._rng = MersenneTwisterUniformRng(seeds=init)

        for i in range(skip):
            self._rng.next_int32()
