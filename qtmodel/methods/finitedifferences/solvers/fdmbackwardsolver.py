from enum import Enum
import math

from qtmodel.error import QTError
from qtmodel.mathconstants import M_SQRT2
from qtmodel.methods.finitedifferences.finitedifferencemodel import FiniteDifferenceModel
from qtmodel.methods.finitedifferences.operators.fdmlinearopcomposite import FdmLinearOpComposite
from qtmodel.methods.finitedifferences.schemes.craigsneydscheme import CraigSneydScheme
from qtmodel.methods.finitedifferences.schemes.cranknicolsonscheme import CrankNicolsonScheme
from qtmodel.methods.finitedifferences.schemes.douglasscheme import DouglasScheme
from qtmodel.methods.finitedifferences.schemes.expliciteulerscheme import ExplicitEulerScheme
from qtmodel.methods.finitedifferences.schemes.hundsdorferscheme import HundsdorferScheme
from qtmodel.methods.finitedifferences.schemes.impliciteulerscheme import ImplicitEulerScheme
from qtmodel.methods.finitedifferences.schemes.methodoflinesscheme import MethodOfLinesScheme
from qtmodel.methods.finitedifferences.schemes.modifiedcraigsneydscheme import ModifiedCraigSneydScheme
from qtmodel.methods.finitedifferences.schemes.trbdf2scheme import TrBDF2Scheme
from qtmodel.methods.finitedifferences.stepconditions.fdmstepconditioncomposite import FdmStepConditionComposite
from qtmodel.methods.finitedifferences.utilities.fdmboundaryconditionset import FdmBoundaryConditionSet
from qtmodel.types import Real


class FdmSchemeTypes(Enum):
    HundsdorferType = "HundsdorferType"
    DouglasType = "DouglasType"
    CraigSneydType = "CraigSneydType"
    ModifiedCraigSneydType = "ModifiedCraigSneydType"
    ImplicitEulerType = "ImplicitEulerType"
    ExplicitEulerType = "ExplicitEulerType"
    MethodOfLinesType = "MethodOfLinesType"
    TrBDF2Type = "TrBDF2Type"
    CrankNicolsonType = "CrankNicolsonType"


class FdmSchemeDesc:
    def __init__(self, a_type: FdmSchemeTypes, a_theta: Real, a_mu: Real):
        self.type = a_type
        self.theta = a_theta
        self.mu = a_mu

    # some default scheme descriptions
    @staticmethod
    def douglas():
        return FdmSchemeDesc(FdmSchemeTypes.DouglasType, 0.5, 0.0)

    @staticmethod
    def crank_nicolson():
        return FdmSchemeDesc(FdmSchemeTypes.CrankNicolsonType, 0.5, 0.0)

    @staticmethod
    def implicit_euler():
        return FdmSchemeDesc(FdmSchemeTypes.ImplicitEulerType, 0.0, 0.0)

    @staticmethod
    def explicit_euler():
        return FdmSchemeDesc(FdmSchemeTypes.ExplicitEulerType, 0.0, 0.0)

    @staticmethod
    def craig_sneyd():
        return FdmSchemeDesc(FdmSchemeTypes.CraigSneydType, 0.5, 0.5)

    @staticmethod
    def modified_craig_sneyd():
        return FdmSchemeDesc(FdmSchemeTypes.ModifiedCraigSneydType, 1.0 / 3.0, 1.0 / 3.0)

    @staticmethod
    def hundsdorfer():
        return FdmSchemeDesc(FdmSchemeTypes.HundsdorferType, 0.5 + math.sqrt(3.0) / 6, 0.5)

    @staticmethod
    def modified_hundsdorfer():
        return FdmSchemeDesc(FdmSchemeTypes.HundsdorferType, 1.0 - math.sqrt(2.0) / 2, 0.5)

    @staticmethod
    def method_of_lines(eps=0.001, rel_init_step_size=0.01):
        return FdmSchemeDesc(FdmSchemeTypes.MethodOfLinesType, eps, rel_init_step_size)

    @staticmethod
    def tr_bdf_2():
        return FdmSchemeDesc(FdmSchemeTypes.TrBDF2Type, 2 - M_SQRT2, 1e-8)


class FdmBackwardSolver:

    def __init__(self,
                 map: FdmLinearOpComposite,
                 bc_set: FdmBoundaryConditionSet,
                 condition: FdmStepConditionComposite,
                 scheme_desc: FdmSchemeDesc):
        self._map = map
        self._bc_set = bc_set
        self._condition = condition if condition is not None else FdmStepConditionComposite([], [])
        self._scheme_desc = scheme_desc

    def rollback(self,
                 rhs: list,
                 begin: Real,
                 end: Real,
                 steps: int,
                 damping_steps: int):

        delta_t = begin - end
        all_steps = steps + damping_steps
        damping_to = begin - (delta_t * damping_steps) / all_steps

        if (damping_steps != 0) and self._scheme_desc.type != FdmSchemeTypes.ImplicitEulerType:
            implicit_evolver = ImplicitEulerScheme(self._map, self._bc_set)
            damping_model = FiniteDifferenceModel(evolver=implicit_evolver, stopping_times=self._condition.stopping_times())
            damping_model.rollback(rhs, begin, damping_to, damping_steps, self._condition)

        if self._scheme_desc.type == FdmSchemeTypes.HundsdorferType:
            hs_evolver = HundsdorferScheme(self._scheme_desc.theta, self._scheme_desc.mu, self._map, self._bc_set)
            hs_model = FiniteDifferenceModel(evolver=hs_evolver, stopping_times=self._condition.stopping_times())
            hs_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.DouglasType:
            ds_evolver = DouglasScheme(self._scheme_desc.theta, self._map, self._bc_set)
            ds_model = FiniteDifferenceModel(evolver=ds_evolver, stopping_times=self._condition.stopping_times())
            ds_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.CrankNicolsonType:
            cn_evolver = CrankNicolsonScheme(self._scheme_desc.theta, self._map, self._bc_set)
            cn_model = FiniteDifferenceModel(evolver=cn_evolver, stopping_times=self._condition.stopping_times())
            cn_model.rollback(rhs, damping_to, end, steps, self._condition)

        elif self._scheme_desc.type == FdmSchemeTypes.CraigSneydType:
            cs_evolver = CraigSneydScheme(self._scheme_desc.theta, self._scheme_desc.mu, self._map, self._bc_set)
            cs_model = FiniteDifferenceModel(evolver=cs_evolver, stopping_times=self._condition.stopping_times())
            cs_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.ModifiedCraigSneydType:
            cs_evolver = ModifiedCraigSneydScheme(self._scheme_desc.theta, self._scheme_desc.mu, self._map, self._bc_set)
            mcs_model = FiniteDifferenceModel(evolver=cs_evolver, stopping_times=self._condition.stopping_times())
            mcs_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.ImplicitEulerType:
            implicit_evolver = ImplicitEulerScheme(self._map, self._bc_set)
            implicit_model = FiniteDifferenceModel(evolver=implicit_evolver, stopping_times=self._condition.stopping_times())
            implicit_model.rollback(rhs, begin, end, all_steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.ExplicitEulerType:
            explicit_evolver = ExplicitEulerScheme(self._map, self._bc_set)
            explicit_model = FiniteDifferenceModel(evolver=explicit_evolver, stopping_times=self._condition.stopping_times())
            explicit_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.MethodOfLinesType:
            method_of_lines = MethodOfLinesScheme(self._scheme_desc.theta, self._scheme_desc.mu, self._map, self._bc_set)
            mol_model = FiniteDifferenceModel(evolver=method_of_lines, stopping_times=self._condition.stopping_times())
            mol_model.rollback(rhs, damping_to, end, steps, self._condition)
        elif self._scheme_desc.type == FdmSchemeTypes.TrBDF2Type:
            tr_desc = FdmSchemeDesc.craig_sneyd()
            hs_evolver = CraigSneydScheme(tr_desc.theta, tr_desc.mu, self._map, self._bc_set)
            tr_bdf_2 = TrBDF2Scheme(self._scheme_desc.theta, self._map, hs_evolver, self._bc_set, self._scheme_desc.mu)
            tr_bdf_2_model = FiniteDifferenceModel(evolver=tr_bdf_2, stopping_times=self._condition.stopping_times())
            tr_bdf_2_model.rollback(rhs, damping_to, end, steps, self._condition)
        else:
            raise QTError("Unknown scheme type")
