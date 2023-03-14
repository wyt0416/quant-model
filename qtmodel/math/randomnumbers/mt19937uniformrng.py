from typing import List, Optional

from qtmodel.math.randomnumbers.seedgenerator import SeedGenerator
from qtmodel.methods.montecarlo.sample import Sample


class MersenneTwisterUniformRng:
    """
    Uniform random number generator
    Mersenne Twister random number generator of period 2**19937-1

    For more details see http://www.math.keio.ac.jp/matumoto/emt.html
    """

    N = 624  # state size
    M = 397  # shift size
    MATRIX_A = 0x9908b0df  # constant vector a
    UPPER_MASK = 0x80000000  # most significant w-r bits
    LOWER_MASK = 0x7fffffff  # least significant r bits

    def __init__(self, seed: int = 0, seeds: List[int] = None):
        self.mt: List[Optional[int]] = [None] * self.N
        self.mti = None
        if seeds is None:
            self.seed_initialization(seed)
        else:
            self.seed_initialization(19650218)
            i = 1
            j = 0
            _seeds_len = len(seeds)
            k = self.N if self.N > _seeds_len else _seeds_len
            while k != 0:
                self.mt[i] = (self.mt[i] ^ ((self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1664525)) + seeds[
                    j] + j  # non linear
                self.mt[i] &= 0xffffffff  # for WORDSIZE > 32 machines
                i += 1
                j += 1
                if i >= self.N:
                    self.mt[0] = self.mt[self.N - 1]
                    i = 1
                if j >= _seeds_len:
                    j = 0
                k -= 1

            k = self.N - 1
            while k != 0:
                self.mt[i] = (self.mt[i] ^ ((self.mt[i - 1] ^ (self.mt[i - 1] >> 30)) * 1566083941)) - i  # non linear
                self.mt[i] &= 0xffffffff  # for WORDSIZE > 32 machines
                i += 1
                if i >= self.N:
                    self.mt[0] = self.mt[self.N - 1]
                    i = 1
                k -= 1

            self.mt[0] = self.UPPER_MASK  # MSB is 1; assuring non-zero initial array

    def seed_initialization(self, seed: int):
        # initializes mt with a seed
        s = seed if seed != 0 else SeedGenerator().get()
        self.mt[0] = s & 0xffffffff
        for mti in range(1, self.N):
            self.mt[mti] = (1812433253 * (self.mt[mti - 1] ^ (self.mt[mti - 1] >> 30)) + mti)
            # See Knuth TAOCP Vol2. 3rd Ed. P.106 for multiplier.
            # In the previous versions, MSBs of the seed affect
            # only MSBs of the array mt[].
            # 2002/01/09 modified by Makoto Matsumoto
            self.mt[mti] &= 0xffffffff
            # for >32 bit machines

    def next(self):
        """
        returns a sample with weight 1.0 containing a random number
        in the (0.0, 1.0) interval
        """
        return Sample(self.next_real(), 1.0)

    def next_real(self):
        """ return a random number in the (0.0, 1.0)-interval """
        return (self.next_int32() + 0.5) / 4294967296.0

    def next_int32(self):
        """ return a random integer in the [0,0xffffffff]-interval """
        if self.mti == self.N:
            self.twist()  # generate N words at a time

        y = self.mt[self.mti]
        self.mti += 1

        # Tempering
        y ^= (y >> 11)
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= (y >> 18)
        return y

    def twist(self):
        mag01 = [0x0, self.MATRIX_A]
        # mag01[x] = x * MATRIX_A  for x=0,1

        kk = 0
        while kk < self.N - self.M:
            y = (self.mt[kk] & self.UPPER_MASK) | (self.mt[kk + 1] & self.LOWER_MASK)
            self.mt[kk] = self.mt[kk + self.M] ^ (y >> 1) ^ mag01[y & 0x1]
            kk += 1
        while kk < self.N - 1:
            y = (self.mt[kk] & self.UPPER_MASK) | (self.mt[kk + 1] & self.LOWER_MASK)
            self.mt[kk] = self.mt[(kk + self.M) - self.N] ^ (y >> 1) ^ mag01[y & 0x1]
            kk += 1

        y = (self.mt[self.N - 1] & self.UPPER_MASK) | (self.mt[0] & self.LOWER_MASK)
        self.mt[self.N - 1] = self.mt[self.M - 1] ^ (y >> 1) ^ mag01[y & 0x1]

        self.mti = 0
