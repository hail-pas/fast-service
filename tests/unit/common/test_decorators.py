import enum
import time
import unittest

from common.decorators import partial, timelimit, extend_enum


def test_partial():
    def func(a, b, c):
        return a + b + c

    # 测试正常情况
    new_func = partial(func, 1, 2)
    assert new_func(3) == 6

    # 测试传入更多的参数
    new_func = partial(func, 1)
    assert new_func(2, 3) == 6

    # 测试传入更少的参数
    new_func = partial(func, 1, 2, 3)
    assert new_func() == 6


class TestTimeLimitDecorator(unittest.TestCase):
    def test_function_within_time_limit(self):
        # Test when the function returns within the specified time limit
        @timelimit(1)
        def function_within_time_limit():
            time.sleep(0.1)
            return "Function completed within time limit"

        result = function_within_time_limit()
        self.assertEqual(result, "Function completed within time limit")

    def test_function_exceeds_time_limit(self):
        # Test when the function exceeds the specified time limit
        @timelimit(0.1)
        def function_exceeds_time_limit():
            time.sleep(1)
            return "This function should not complete within time limit"

        with self.assertRaises(RuntimeError):
            function_exceeds_time_limit()

    def test_function_raises_error(self):
        # Test when the function raises an error
        @timelimit(1)
        def function_raises_error():
            time.sleep(0.5)
            raise ValueError("Function raised an error")

        with self.assertRaises(ValueError):
            function_raises_error()

    def test_timeout_as_float(self):
        # Test when the timeout argument is passed as a float
        @timelimit(1.0)
        def function_within_time_limit():
            time.sleep(0.5)
            return "Function completed within time limit"

        result = function_within_time_limit()
        self.assertEqual(result, "Function completed within time limit")

    def test_timeout_as_int(self):
        # Test when the timeout argument is passed as an integer
        @timelimit(1)
        def function_within_time_limit():
            time.sleep(0.5)
            return "Function completed within time limit"

        result = function_within_time_limit()
        self.assertEqual(result, "Function completed within time limit")


def test_extend_enum():
    class BaseEnum(enum.Enum):
        FOO = 1
        BAR = 2

    @extend_enum(BaseEnum)
    class AdditionalEnum(enum.Enum):
        BAZ = 3
        QUUX = 4

    assert AdditionalEnum.FOO.value == 1
    assert AdditionalEnum.BAR.value == 2
    assert AdditionalEnum.BAZ.value == 3
    assert AdditionalEnum.QUUX.value == 4
