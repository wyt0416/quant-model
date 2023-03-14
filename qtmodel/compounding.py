from enum import Enum


class Compounding(Enum):
    """ Interest rate coumpounding rule """
    Simple = 0,  # 1+rt
    Compounded = 1,  # (1+r)^t
    Continuous = 2,  # e^{rt}
    SimpleThenCompounded = 3,  # Simple up to the first period then Compounded
    CompoundedThenSimple = 4  # Compounded up to the first period then Simple
