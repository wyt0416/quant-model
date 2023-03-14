from datetime import datetime

from qtmodel.exercise import EuropeanExercise
from qtmodel.handle import Handle
from qtmodel.instruments.payoffs import PlainVanillaPayoff
from qtmodel.instruments.vanillaoption import VanillaOption
from qtmodel.option import OptionTypes
from qtmodel.pricingengines.vanilla.analyticeuropeanengine import AnalyticEuropeanEngine
from qtmodel.processes.blackscholesprocess import BlackScholesMertonProcess
from qtmodel.quotes.simplequote import SimpleQuote
from qtmodel.settings import Settings
from qtmodel.termstructures.volatility.equityfx.blackconstantvol import BlackConstantVol
from qtmodel.termstructures.yield_curve.flatforward import FlatForward
from qtmodel.time.calendars.target import TARGET

# set up dates
from qtmodel.time.date import DateTool
from qtmodel.time.daycounters.actual365fixed import Actual365Fixed
from qtmodel.time.timeunit import TimeUnit

calendar = TARGET()
todays_date = datetime(1998, 5, 15)
settlement_date = datetime(1998, 5, 17)
Settings().evaluation_date = todays_date

# our options
option_type = OptionTypes.Put
underlying = 36
strike = 40
dividend_yield = 0.00
risk_free_rate = 0.06
volatility = 0.20
maturity = datetime(1999, 5, 17)
day_counter = Actual365Fixed()

print(f"""Option type = {option_type}
Maturity = {maturity}
Underlying price = {underlying}
Strike = {strike}
Risk-free interest rate = {risk_free_rate:.2%}                 
Dividend yield = {dividend_yield:.2%}    
Volatility = {volatility:.2%}""")

exercise_dates = []
for i in range(1, 5):
    exercise_dates.append(DateTool.advance(date=settlement_date,
                                           n=3*i,
                                           units=TimeUnit.Months))

european_exercise = EuropeanExercise(maturity)
underlying_h = Handle(SimpleQuote(underlying))

# bootstrap the yield/dividend/vol curves
flat_term_structure = Handle(FlatForward(reference_date=settlement_date,
                                         forward=risk_free_rate,
                                         day_counter=day_counter))
flat_dividend_ts = Handle(FlatForward(reference_date=settlement_date,
                                      forward=dividend_yield,
                                      day_counter=day_counter))
flat_vol_ts = Handle(BlackConstantVol(reference_date=settlement_date,
                                      cal=calendar,
                                      volatility=volatility,
                                      dc=day_counter))
payoff = PlainVanillaPayoff(option_type, strike)
bsm_process = BlackScholesMertonProcess(x0=underlying_h,
                                        dividend_ts=flat_dividend_ts,
                                        risk_free_ts=flat_term_structure,
                                        black_vol_ts=flat_vol_ts)

# options
european_option = VanillaOption(payoff, european_exercise)

# Black-Scholes for European
european_option.set_pricing_engine(AnalyticEuropeanEngine(bsm_process))
print(f"Black-Scholes: {european_option.NPV():.6f}")

# # Vasicek rates model for European
# r0 = risk_free_rate
# a = 0.3
# b = 0.3
# sigma_r = 0.15
# riskPremium = 0.0
# correlation = 0.5
# vasicek_process = Vasicek(r0, a, b, sigma_r, riskPremium)
# european_option.set_pricing_engine(AnalyticBlackVasicekEngine(bsm_process, vasicek_process, correlation))
# print(f"Black Vasicek Model: {european_option.NPV():.6f}")
#
# # semi-analytic Heston for European
# heston_process = HestonProcess(flat_term_structure, flat_dividend_ts,
#                                underlying_h, volatility*volatility,
#                                1.0, volatility*volatility, 0.001, 0.0)
# heston_model = HestonModel(heston_process)
# europeanOption.set_pricing_engine(AnalyticHestonEngine(heston_model))
# print(f"Heston semi-analytic: {european_option.NPV():.6f}")
#
# # semi-analytic Bates for European
# bates_process = BatesProcess(flat_term_structure, flat_dividend_ts,
#                              underlying_h, volatility*volatility,
#                              1.0, volatility*volatility, 0.001, 0.0,
#                              1e-14, 1e-14, 1e-14)
# bates_model = BatesModel(bates_process)
# european_option.set_pricing_engine(BatesEngine(bates_model))
# print(f"Bates semi-analytic: {european_option.NPV():.6f}")