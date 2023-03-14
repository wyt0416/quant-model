from qtmodel.error import qt_require
from qtmodel.methods.finitedifferences.meshers.fdmmesher import FdmMesher
from qtmodel.methods.finitedifferences.stepcondition import StepCondition
from qtmodel.methods.finitedifferences.utilities.fdminnervaluecalculator import FdmInnerValueCalculator
from qtmodel.types import Real


class FdmAmericanStepCondition(StepCondition):

    def __init__(self,
                 mesher: FdmMesher,
                 calculator: FdmInnerValueCalculator):
        self._mesher = mesher
        self._calculator = calculator
        self._exercise_times = []

    def apply_to(self, a: list, t: Real):
        layout = self._mesher.layout()

        qt_require(layout.size() == len(a),
                   "inconsistent array dimensions")

        end_iter = layout.end()

        i = layout.begin()
        while i != end_iter:
            inner_value = self._calculator.inner_value(i, t)
            if inner_value > a[i.index()]:
                a[i.index()] = inner_value

            i.increment()

