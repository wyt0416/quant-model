import math
from typing import Union, List

import numpy as np

from qtmodel.error import qt_require


def generate_array(size: int,
                   value: Union[float, int],
                   increment: Union[float, int]):
    return [value + i * increment for i in range(size)]


def dot_product(v1: List, v2: List):
    qt_require(len(v1) == len(v2), f"arrays with different sizes ({len(v1)},{len(v2)}) cannot be multiplied")
    return sum(np.multiply(v1, v2))


def norm_2(v):
    return math.sqrt(dot_product(v, v))


# 返回nums中第一个>target的值的位置，如果nums中都不比target大，则返回len(nums)
def upper_bound(nums: list, target):
    low, high = 0, len(nums) - 1
    pos = len(nums)
    while low < high:
        mid = int((low + high) / 2)
        if nums[mid] <= target:
            low = mid + 1
        else:  # >
            high = mid
            pos = high
    if nums[low] > target:
        pos = low
    return pos


# 返回nums中第一个>=target的值得位置，如果nums中都比target小，则返回len(nums)
def lower_bound(nums, target):
    low, high = 0, len(nums) - 1
    pos = len(nums)
    while low < high:
        mid = int((low + high) / 2)
        if nums[mid] < target:
            low = mid + 1
        else:  # >=
            high = mid
            # pos = high
    if nums[low] >= target:
        pos = low
    return pos
