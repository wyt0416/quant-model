from typing import Union

from qtmodel.compounding import Compounding
from qtmodel.error import QTError
from qtmodel.patterns.observable import Observable
from qtmodel.termstructures.volatility.equityfx.blackvoltermstructure import BlackVolTermStructure
from qtmodel.termstructures.yieldtermstructure import YieldTermStructure
from qtmodel.types import Real


class FdmQuantoHelper(Observable):
    def __init__(self,
                 r_ts: YieldTermStructure=None,
                 f_ts: YieldTermStructure=None,
                 fx_vol_ts: BlackVolTermStructure=None,
                 equity_fx_correlation: Real=None,
                 exch_rate_atm_level: Real=None):
        super(FdmQuantoHelper, self).__init__()
        self._r_ts = r_ts
        self._f_ts = f_ts
        self._fx_vol_ts = fx_vol_ts
        self._equity_fx_correlation = equity_fx_correlation
        self._exch_rate_atm_level = exch_rate_atm_level

    def quanto_adjustment(self, equity_vol: Union[Real, list], t1: Real, t2: Real):
        if isinstance(equity_vol, (int, float)):
            r_domestic = self._r_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()
            r_foreign = self._f_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()
            fx_vol = self._fx_vol_ts.black_forward_vol(t1, t2, self._exch_rate_atm_level)

            return r_domestic - r_foreign + equity_vol * fx_vol * self._equity_fx_correlation
        elif isinstance(equity_vol, list):
            r_domestic = self._r_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()
            r_foreign = self._f_ts.forward_rate(t1=t1, t2=t2, comp=Compounding.Continuous).rate()
            fx_vol = self._fx_vol_ts.black_forward_vol(t1, t2, self._exch_rate_atm_level)

            ret_val = [None] * len(equity_vol)
            for i in range(len(ret_val)):
                ret_val[i] = r_domestic - r_foreign + equity_vol[i] * fx_vol * self._equity_fx_correlation

            return ret_val
        else:
            raise QTError("equity_vol must be real or list.")
