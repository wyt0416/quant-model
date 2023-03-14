import sys
from abc import ABCMeta, abstractmethod
from typing import Optional

from qtmodel.error import qt_require, QTError
from qtmodel.types import Real


class ConstraintImpl(metaclass=ABCMeta):
    """ Base class for constraint implementations """

    @abstractmethod
    def test(self, params: list) -> bool:
        """
        Tests if params satisfy the constraint
        :param params:
        :return:
        """
        pass

    @abstractmethod
    def upper_bound(self, params: list) -> list:
        """
        Returns upper bound for given parameters
        :param params:
        :return:
        """
        return [sys.float_info.max] * len(params)

    @abstractmethod
    def lower_bound(self, params: list) -> list:
        """
        Returns lower bound for given parameters
        :param params:
        :return:
        """
        return [-sys.float_info.max] * len(params)


class Constraint:
    """ Base constraint class """

    def __init__(self, impl: Optional[ConstraintImpl]):
        self._impl = impl

    def empty(self) -> bool:
        return self._impl is None

    def test(self, p: list):
        return self._impl.test(p)

    def upper_bound(self, params: list):
        result = self._impl.upper_bound(params)
        _params_len = len(params)
        _result_len = len(result)
        qt_require(_params_len == _result_len,
                   f"upper bound size ({_result_len}) not equal to params size ({_params_len})")
        return result

    def lower_bound(self, params: list):
        result = self._impl.lower_bound(params)
        _params_len = len(params)
        _result_len = len(result)
        qt_require(_params_len == _result_len,
                   f"lower bound size ({_result_len}) not equal to params size ({_params_len})")
        return result

    def update(self, params: list, direction: list, beta: Real):
        diff = beta
        new_params = [i + j for i, j in zip(params, [i * diff for i in direction])]
        valid = self.test(new_params)
        icount = 0
        while not valid:
            if icount > 200:
                QTError("can't update parameter vector")
            diff *= 0.5
            icount += 1
            new_params = [i + j for i, j in zip(params, [i * diff for i in direction])]
            valid = self.test(new_params)

        params = [i + j for i, j in zip(params, [i * diff for i in direction])]
        return diff, params


class NoConstraintImpl(ConstraintImpl):

    def test(self, params: list) -> bool:
        return True


class NoConstraint(Constraint):
    """ No constraint """

    def __init__(self):
        super().__init__(NoConstraintImpl())


class PositiveConstraintImpl(ConstraintImpl):

    def test(self, params: list):
        return all(_ > 0.0 for _ in params)

    def upper_bound(self, params: list):
        return [sys.float_info.max] * len(params)

    def lower_bound(self, params: list):
        return [0.0] * len(params)


class PositiveConstraint(Constraint):
    """ Constraint imposing positivity to all arguments """

    def __init__(self):
        super().__init__(PositiveConstraintImpl())


class BoundaryConstraintImpl(ConstraintImpl):

    def __init__(self, low: Real, high: Real):
        self._low = low
        self._high = high

    def test(self, params: list):
        return all(self._low <= _ <= self._high for _ in params)

    def upper_bound(self, params: list):
        return [self._high] * len(params)

    def lower_bound(self, params: list):
        return [self._low] * len(params)


class BoundaryConstraint(Constraint):
    """ Constraint imposing all arguments to be in [low,high] """

    def __init__(self, low: Real, high: Real):
        super().__init__(BoundaryConstraintImpl(low, high))


class CompositeConstraintImpl(ConstraintImpl):

    def __init__(self, c1: Constraint, c2: Constraint):
        self._c1 = c1
        self._c2 = c2

    def test(self, params: list):
        return self._c1.test(params) and self._c2.test(params)

    def upper_bound(self, params: list):
        c1ub = self._c1.upper_bound(params)
        c2ub = self._c2.upper_bound(params)
        _c1ub_len = len(c1ub)
        rtrn_array = [0.0] * _c1ub_len
        for i in range(_c1ub_len):
            rtrn_array[i] = min(c1ub[i], c2ub[i])
        return rtrn_array

    def lower_bound(self, params: list):
        c1lb = self._c1.lower_bound(params)
        c2lb = self._c2.lower_bound(params)
        _c1lb_len = len(c1lb)
        rtrn_array = [0.0] * _c1lb_len
        for i in range(_c1lb_len):
            rtrn_array[i] = max(c1lb[i], c2lb[i])
        return rtrn_array


class CompositeConstraint(Constraint):
    """ Constraint enforcing both given sub-constraints """

    def __init__(self, c1: Constraint, c2: Constraint):
        super().__init__(CompositeConstraintImpl(c1, c2))


class NonhomogeneousBoundaryConstraintImpl(ConstraintImpl):

    def __init__(self, low: list, high: list):
        qt_require(len(low) == len(high),
                   "Upper and lower boundaries sizes are inconsistent.")
        self._low = low
        self._high = high

    def test(self, params: list):
        _params_len = len(params)
        qt_require(_params_len == len(self._low),
                   "Number of parameters and boundaries sizes are inconsistent.")
        for i in range(_params_len):
            if (params[i] < self._low[i]) or (params[i] > self._high[i]):
                return False
        return True

    def upper_bound(self, params: list):
        return self._high

    def lower_bound(self, params: list):
        return self._low


class NonhomogeneousBoundaryConstraint(Constraint):
    """ Constraint imposing i-th argument to be in [low_i,high_i] for all i """

    def __init__(self, low: list, high: list):
        super().__init__(NonhomogeneousBoundaryConstraintImpl(low, high))
