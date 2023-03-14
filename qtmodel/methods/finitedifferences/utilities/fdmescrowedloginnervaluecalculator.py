import math

from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.operators.fdmlinearopiterator import FdmLinearOpIterator
from qtmodel.methods.finitedifferences.utilities.escroweddividendadjustment import EscrowedDividendAdjustment
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmInnerValueCalculator
from qtmodel.payoff import Payoff
from qtmodel.types import Real


class FdmEscrowedLogInnerValueCalculator(FdmInnerValueCalculator):
    def __init__(self,
                 escrowed_dividend_adj: EscrowedDividendAdjustment,
                 payoff: Payoff,
                 mesher: FdmMesher,
                 direction: int):
        self._escrowed_dividend_adj = escrowed_dividend_adj
        self._payoff = payoff
        self._mesher = mesher
        self._direction = direction

    def inner_value(self, iter: FdmLinearOpIterator, t: Real):
        s_t = math.exp(self._mesher.location(iter, self._direction))
        spot = s_t - self._escrowed_dividend_adj.dividend_adjustment(t)

        return self._payoff(spot)

    def avg_inner_value(self, iter: FdmLinearOpIterator, t: Real):
        return self.inner_value(iter, t)
