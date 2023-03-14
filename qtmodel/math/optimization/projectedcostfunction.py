from typing import List

from qtmodel.error import QTError
from qtmodel.math.optimization.costfunction import CostFunction
from qtmodel.math.optimization.projection import Projection


class ProjectedCostFunction(CostFunction, Projection):
    """
    Parameterized cost function
    This class creates a proxy cost function which can depend
    on any arbitrary subset of parameters (the other being fixed)
    """

    def __init__(self,
                 cost_function: CostFunction,
                 parameter_values: list = None,
                 fix_parameters: List[bool] = None,
                 projection: Projection = None):
        if projection is None and parameter_values is not None and fix_parameters is not None:
            Projection.__init__(self, parameter_values, fix_parameters)
            self._cost_function = cost_function
        elif projection is not None:
            Projection.__init__(self, projection._fixed_parameters, projection._fix_parameters)
            self._cost_function = cost_function
        else:
            raise QTError("parameter_values and fix_parameters must be passed together. "
                          "If parameter_values and fix_parameters are not passed, projection must be passed")

    def value(self, free_parameters: list):
        self.map_free_parameters(free_parameters)
        return self._cost_function.value(self._actual_parameters)

    def values(self, free_parameters: list):
        self.map_free_parameters(free_parameters)
        return self._cost_function.values(self._actual_parameters)
