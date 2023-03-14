from datetime import datetime
from qtmodel.cashflow import CashFlow
from qtmodel.error import qt_require
from qtmodel.types import Real


class SimpleCashFlow(CashFlow):
    '''
    Predetermined cash flow
     This cash flow pays a predetermined amount at a given date.
    '''

    def __init__(self, amount: Real, date: datetime):
        self._amount = amount
        self._date = date
        qt_require(self._amount is not None, "null date SimpleCashFlow")
        qt_require(self._date is not None, "null amount SimpleCashFlow")

    def date(self):
        return self._date

    def amount(self):
        return self._amount
# @}
# ! \name Visitability
# @{
# C++ TO PYTHON CONVERTER TODO TASK: The implementation of the following method could not be found:
#    accept(UnnamedParameter)
# @}

    #! Bond redemption
    #    ! This class specializes SimpleCashFlow so that visitors
    #        can perform more detailed cash-flow analysis.
    #
class Redemption(SimpleCashFlow):
    def __init__(self, amount, date):
        super().__init__(amount, date)
    #! \name Visitability
    #@{
    def accept(self, v):
        v1 =  if isinstance(v, Visitor<Redemption>) else None
        if v1 is not None:
            v1.visit(self)
        else:
            super().accept(v)

    #@}

#! Amortizing payment
#    ! This class specializes SimpleCashFlow so that visitors
#        can perform more detailed cash-flow analysis.
#
class AmortizingPayment(SimpleCashFlow):
    def __init__(self, amount, date):
        super().__init__(amount, date)
    #! \name Visitability
    #@{
    def accept(self, v):
        v1 =  if isinstance(v, Visitor<AmortizingPayment>) else None
        if v1 is not None:
            v1.visit(self)
        else:
            super().accept(v)
