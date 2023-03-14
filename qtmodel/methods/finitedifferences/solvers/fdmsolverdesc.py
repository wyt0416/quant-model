from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.stepconditions.fdmstepconditioncomposite import FdmStepConditionComposite
from qtmodel.methods.finitedifferences.utilities.fdmboundaryconditionset import FdmBoundaryConditionSet
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmInnerValueCalculator
from qtmodel.types import Real


class FdmSolverDesc:

    def __init__(self,
                 mesher: FdmMesher,
                 bc_set: FdmBoundaryConditionSet,
                 condition: FdmStepConditionComposite,
                 calculator: FdmInnerValueCalculator,
                 maturity: Real,
                 time_steps: int,
                 damping_steps: int):
        self.mesher = mesher
        self.bc_set = bc_set
        self.condition = condition
        self.calculator = calculator
        self.maturity = maturity
        self.time_steps = time_steps
        self.damping_steps = damping_steps
