from enum import Enum

from qtmodel.cashflows.dividend import FixedDividend
from qtmodel.error import qt_require, QTError
from qtmodel.exercise import ExerciseTypes
from qtmodel.handle import Handle
from qtmodel.instruments.dividendschedule import DividendSchedule
from qtmodel.instruments.dividendvanillaoptionEngine import DividendVanillaOptionEngine
from qtmodel.methods.finitedifferences.meshers.fdmblackscholesmesher import FdmBlackScholesMesher
from qtmodel.methods.finitedifferences.meshers.fdmmeshercomposite import FdmMesherComposite
from qtmodel.methods.finitedifferences.solvers.fdmbackwardsolver import FdmSchemeDesc
from qtmodel.methods.finitedifferences.solvers.fdmblackscholessolver import FdmBlackScholesSolver
from qtmodel.methods.finitedifferences.solvers.fdmsolverdesc import FdmSolverDesc
from qtmodel.methods.finitedifferences.stepconditions.fdmstepconditioncomposite import FdmStepConditionComposite
from qtmodel.methods.finitedifferences.utilities.escroweddividendadjustment import EscrowedDividendAdjustment
from qtmodel.methods.finitedifferences.utilities.fdmescrowedloginnervaluecalculator import \
    FdmEscrowedLogInnerValueCalculator
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmLogInnerValue
from qtmodel.methods.finitedifferences.utilities.fdmquantohelper import FdmQuantoHelper
from qtmodel.processes.blackscholesprocess import GeneralizedBlackScholesProcess
from qtmodel.types import Real


class CashDividendModel(Enum):
    Spot = "Spot"
    Escrowed = "Escrowed"


class FdBlackScholesVanillaEngine(DividendVanillaOptionEngine):

    def __init__(self,
                 process: GeneralizedBlackScholesProcess,
                 quanto_helper: FdmQuantoHelper = None,
                 t_grid: int = 100,
                 x_grid: int = 100,
                 damping_steps: int = 0,
                 scheme_desc: FdmSchemeDesc = FdmSchemeDesc.douglas(),
                 local_vol: bool = False,
                 illegal_local_vol_overwrite: Real = None,
                 cash_dividend_model: CashDividendModel = CashDividendModel.Spot):
        super(FdBlackScholesVanillaEngine, self).__init__()
        self._process = process
        self._t_grid = t_grid
        self._x_grid = x_grid
        self._damping_steps = damping_steps
        self._scheme_desc = scheme_desc
        self._local_vol = local_vol
        self._illegal_local_vol_overwrite = illegal_local_vol_overwrite
        self._quanto_helper = quanto_helper
        self._cash_dividend_model = cash_dividend_model

        self.register_with(self._process)
        if self._quanto_helper is not None:
            self.register_with(self._quanto_helper)

    def calculate(self):
        # 0. Cash dividend model
        exercise_date = self._arguments.exercise.last_date()
        maturity = self._process.time(exercise_date)
        settlement_date = self._process.risk_free_rate().reference_date()

        spot_adjustment = 0.0
        dividend_schedule: DividendSchedule = []

        escrowed_div_adj = None

        if self._cash_dividend_model == CashDividendModel.Spot:
            dividend_schedule = self._arguments.cash_flow
        elif self._cash_dividend_model == CashDividendModel.Escrowed:
            if self._arguments.exercise.type() != ExerciseTypes.European:
                # add dividend dates as stopping times
                for cf in self._arguments.cash_flow:
                    dividend_schedule.append(FixedDividend(0.0, cf.date()))

            qt_require(self._quanto_helper is None, "Escrowed dividend model is not supported for Quanto-Options")

            escrowed_div_adj = EscrowedDividendAdjustment(self._arguments.cash_flow,
                                                          self._process.risk_free_rate(),
                                                          self._process.dividend_yield(),
                                                          lambda d: self._process.time(d),
                                                          maturity)

            spot_adjustment = escrowed_div_adj.dividend_adjustment(self._process.time(settlement_date))

            qt_require(self._process.x0() + spot_adjustment > 0.0, "spot minus dividends becomes negative")

        else:
            raise QTError("unknwon cash dividend model")

        # 1. Mesher
        payoff = self._arguments.payoff

        equity_mesher = FdmBlackScholesMesher(self._x_grid,
                                              self._process,
                                              maturity,
                                              payoff.strike(),
                                              None,
                                              None,
                                              0.0001,
                                              1.5,
                                              (payoff.strike(), 0.1),
                                              dividend_schedule,
                                              self._quanto_helper,
                                              spot_adjustment)

        mesher = FdmMesherComposite(mesher=equity_mesher)

        # 2. Calculator
        if self._cash_dividend_model == CashDividendModel.Spot:
            calculator = FdmLogInnerValue(payoff, mesher, 0)
        elif self._cash_dividend_model == CashDividendModel.Escrowed:
            calculator = FdmEscrowedLogInnerValueCalculator(escrowed_div_adj, payoff, mesher, 0)
        else:
            raise QTError("unknwon cash dividend model")

        # 3. Step conditions
        conditions = FdmStepConditionComposite.vanilla_composite(dividend_schedule,
                                                                 self._arguments.exercise,
                                                                 mesher,
                                                                 calculator,
                                                                 self._process.risk_free_rate().reference_date(),
                                                                 self._process.risk_free_rate().day_counter())

        # 4. Boundary conditions
        boundaries = []

        # 5. Solver
        solver_desc = FdmSolverDesc(mesher, boundaries, conditions, calculator, maturity, self._t_grid,
                                    self._damping_steps)

        solver = FdmBlackScholesSolver(Handle(self._process),
                                       payoff.strike(),
                                       solver_desc,
                                       self._scheme_desc,
                                       self._local_vol,
                                       self._illegal_local_vol_overwrite,
                                       Handle(self._quanto_helper) if self._quanto_helper is not None else Handle(FdmQuantoHelper()))

        spot = self._process.x0() + spot_adjustment

        self._results.value = solver.value_at(spot)
        self._results.delta = solver.delta_at(spot)
        self._results.gamma = solver.gamma_at(spot)
        self._results.theta = solver.theta_at(spot)


class MakeFdBlackScholesVanillaEngine:

    def __init__(self, process: GeneralizedBlackScholesProcess):
        self._process = process
        self._t_grid = 100
        self._x_grid = 100
        self._damping_steps = 0
        self._scheme_desc = FdmSchemeDesc.douglas()
        self._local_vol = False
        self._illegal_local_vol_overwrite = None
        self._quanto_helper = None
        self._cash_dividend_model = CashDividendModel.Spot

    def with_quanto_helper(self, quanto_helper: FdmQuantoHelper):
        self._quanto_helper = quanto_helper
        return self

    def with_t_grid(self, t_grid: int):
        self._t_grid = t_grid
        return self

    def with_x_grid(self, x_grid: int):
        self._x_grid = x_grid
        return self

    def with_damping_steps(self, damping_steps: int):
        self._damping_steps = damping_steps
        return self

    def with_fdm_scheme_desc(self, scheme_desc: FdmSchemeDesc):
        self._scheme_desc = scheme_desc
        return self

    def with_local_vol(self, local_vol: bool):
        self._local_vol = local_vol
        return self

    def with_illegal_local_vol_overwrite(self, illegal_local_vol_overwrite: Real):
        self._illegal_local_vol_overwrite = illegal_local_vol_overwrite
        return self

    def with_cash_dividend_model(self, cash_dividend_model: CashDividendModel):
        self._cash_dividend_model = cash_dividend_model
        return self

    def __call__(self):
        return FdBlackScholesVanillaEngine(self._process,
                                           self._quanto_helper,
                                           self._t_grid,
                                           self._x_grid,
                                           self._damping_steps,
                                           self._scheme_desc,
                                           self._local_vol,
                                           self._illegal_local_vol_overwrite,
                                           self._cash_dividend_model)
