import datetime
import unittest
from zoneinfo import ZoneInfo

from common.utils import (
    mapper,
    commify,
    format_str_to_seconds,
    seconds_to_format_str,
    generate_random_string,
)


class TestGenerateRandomString(unittest.TestCase):
    def test_generates_correct_length(self):
        length = 10
        result = generate_random_string(length)
        self.assertEqual(len(result), length)

    def test_generates_only_digits(self):
        length = 10
        result = generate_random_string(length, all_digits=True)
        self.assertTrue(result.isdigit())

    def test_excludes_given_characters(self):
        length = 10
        excludes = ["a", "b", "c"]
        result = generate_random_string(length, excludes=excludes)
        for char in excludes:
            self.assertNotIn(char, result)


class TestCommify(unittest.TestCase):
    def test_positive_int(self):
        self.assertEqual(commify(1), "1")
        self.assertEqual(commify(123), "123")
        self.assertEqual(commify(1234), "1,234")
        self.assertEqual(commify(1234567890), "1,234,567,890")

    def test_negative_int(self):
        self.assertEqual(commify(-1), "-1")
        self.assertEqual(commify(-123), "-123")
        self.assertEqual(commify(-1234), "-1,234")
        self.assertEqual(commify(-1234567890), "-1,234,567,890")

    def test_positive_float(self):
        self.assertEqual(commify(123.0), "123.0")
        self.assertEqual(commify(1234.5), "1,234.5")
        self.assertEqual(commify(1234.56789), "1,234.56789")

    def test_negative_float(self):
        self.assertEqual(commify(-123.0), "-123.0")
        self.assertEqual(commify(-1234.5), "-1,234.5")
        self.assertEqual(commify(-1234.56789), "-1,234.56789")

    def test_string_input(self):
        self.assertRaises(TypeError, commify, "123")
        self.assertRaises(TypeError, commify, "12.34")

    def test_none_input(self):
        self.assertEqual(commify(None), None)


class TestMapper(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(mapper(lambda x: x, []), [])

    def test_list(self):
        self.assertEqual(mapper(lambda x: x * 2, [1, 2, 3]), [2, 4, 6])

    def test_empty_dict(self):
        self.assertEqual(mapper(lambda x: x, {}), {})

    def test_dict(self):
        self.assertEqual(
            mapper(lambda x: x * 2, {"a": 1, "b": 2}),
            {"a": 2, "b": 4},
        )

    def test_nested_dict(self):
        self.assertEqual(
            mapper(lambda x: x * 2, {"a": {"b": 1, "c": 2}}),
            {"a": {"b": 2, "c": 4}},
        )

    def test_nested_list(self):
        self.assertEqual(
            mapper(lambda x: x * 2, [[1, 2], [3, 4]]),
            [[2, 4], [6, 8]],
        )

    def test_mixed_list(self):
        self.assertEqual(
            mapper(lambda x: x * 2, [1, {"a": 2}, [3]]),
            [2, {"a": 4}, [6]],
        )

    def test_mixed_dict(self):
        self.assertEqual(
            mapper(lambda x: x * 2, {"a": [1, 2], "b": {"c": 3}}),
            {"a": [2, 4], "b": {"c": 6}},
        )


class TestTimeConversion(unittest.TestCase):
    def test_seconds_to_format_str_default(self):
        self.assertEqual(seconds_to_format_str(0), "1970-01-01 08:00:00")

    def test_seconds_to_format_str_custom_format(self):
        self.assertEqual(seconds_to_format_str(0, "%Y-%m-%d"), "1970-01-01")

    def test_seconds_to_format_str_with_offset(self):
        self.assertEqual(
            seconds_to_format_str(1682676806632, offset=0.001),
            "2023-04-28 18:13:26",
        )

    def test_seconds_to_format_str_with_tzinfo(self):
        tz = ZoneInfo("America/Los_Angeles")
        self.assertEqual(
            seconds_to_format_str(0, tzinfo=tz),
            "1969-12-31 16:00:00",
        )

    def test_format_str_to_seconds_default(self):
        self.assertEqual(format_str_to_seconds("1970-01-01 08:00:00"), 0)

    def test_format_str_to_seconds_custom_format(self):
        self.assertEqual(
            format_str_to_seconds("1970-01-01", "%Y-%m-%d"),
            -28800,
        )

    def test_format_str_to_seconds_with_tzinfo(self):
        tz = ZoneInfo("UTC")
        self.assertEqual(
            format_str_to_seconds("1970-01-01 00:00:00", tzinfo=tz),
            0,
        )

    def test_format_str_to_seconds_with_datetime(self):
        tz = ZoneInfo("America/Los_Angeles")
        self.assertEqual(
            format_str_to_seconds(
                datetime.datetime(1970, 1, 1, 0, 0, tzinfo=tz),
            ),
            -28800,
        )
