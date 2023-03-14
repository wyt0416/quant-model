from qtmodel.error import qt_require
from qtmodel.handle import Handle
from qtmodel.instrument import Instrument
from qtmodel.math.solvers1d.brent import Brent
from qtmodel.pricingengine import PricingEngine
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.termstructures.volatility.equityfx.blackconstantvol import BlackConstantVol
from qtmodel.types import Real


class PriceError:

    def __init__(self,
                 engine: PricingEngine,
                 vol: SimpleQuote,
                 target_value: Real):
        self._engine = engine
        self._vol = vol
        self._target_value = target_value
        self._results = self._engine.get_results()
        qt_require(self._results is not None, "pricing engine does not supply needed results")

    def __call__(self, x: Real):
        self._vol.set_value(x)
        self._engine.calculate()
        return self._results.value - self._target_value


class ImpliedVolatilityHelper:
    """
    helper class for one-asset implied-volatility calculation
    The passed engine must be linked to the passed quote (see,
    e.g., VanillaOption to see how this can be achieved.)
    """

    @staticmethod
    def calculate(instrument: Instrument,
                  engine: PricingEngine,
                  vol_quote: SimpleQuote,
                  target_value: Real,
                  accuracy: Real,
                  max_evaluations: int,
                  min_vol: Real,
                  max_vol: Real):
        instrument.setup_arguments(engine.get_arguments())
        engine.get_arguments().validate()

        f = PriceError(engine, vol_quote, target_value)
        solver = Brent()
        solver.set_max_evaluations(max_evaluations)
        guess = (min_vol + max_vol) / 2.0
        result = solver.solve(f=f,
                              accuracy=accuracy,
                              guess=guess,
                              x_min=min_vol,
                              x_max=max_vol)
        return result

    @staticmethod
    def clone(process: GeneralizedBlackScholesProcess,
              vol_quote: SimpleQuote):
        state_variable = process.state_variable()
        dividend_yield = process.dividend_yield()
        risk_free_rate = process.risk_free_rate()

        black_vol = process.black_volatility()
        volatility = BlackConstantVol(reference_date=black_vol.reference_date(),
                                      cal=black_vol.calendar(),
                                      volatility=Handle(vol_quote),
                                      dc=black_vol.day_counter())

        return GeneralizedBlackScholesProcess(x0=state_variable,
                                              dividend_ts=dividend_yield,
                                              risk_free_ts=risk_free_rate,
                                              black_vol_ts=volatility)
