import re
import random
import string
import datetime
from typing import Any, Union, Callable
from zoneinfo import ZoneInfo
from collections.abc import Hashable

from starlette.requests import Request

from conf.config import local_configs

DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_STRING = "%Y-%m-%d"


def generate_random_string(
    length: int,
    all_digits: bool = False,
    excludes: list = None,
) -> str:
    """生成任意长度字符串."""
    if excludes is None:
        excludes = []
    all_char = (
        string.digits if all_digits else string.ascii_letters + string.digits
    )
    if excludes:
        for char in excludes:
            all_char = all_char.replace(char, "")
    return "".join(random.sample(all_char, length))


def get_client_ip(request: Request) -> str:
    """获取客户端真实ip
    :param request:
    :return:
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


def datetime_now() -> datetime.datetime:
    # 返回带有时区信息的时间
    return datetime.datetime.now(
        tz=ZoneInfo(local_configs.RELATIONAL.TIMEZONE or "Asia/Shanghai"),
    )


def commify(n: Union[int, float]) -> str | None:
    """Add commas to an integer `n`.
    raise:
        TypeError: type check
    >>> commify(1)
    '1'
    >>> commify(123)
    '123'
    >>> commify(-123)
    '-123'
    >>> commify(1234)
    '1,234'
    >>> commify(1234567890)
    '1,234,567,890'
    >>> commify(123.0)
    '123.0'
    >>> commify(1234.5)
    '1,234.5'
    >>> commify(1234.56789)
    '1,234.56789'
    >>> commify(' %.2f ' % -1234.5)
    '-1,234.50'
    >>> commify(None)
    >>>.
    """
    if n is None:
        return None

    if not isinstance(n, (int, float)):
        raise TypeError("n must be an integer or float.")

    n = str(n).strip()

    if n.startswith("-"):
        prefix = "-"
        n = n[1:].strip()
    else:
        prefix = ""

    if "." in n:
        dollars, cents = n.split(".")
    else:
        dollars, cents = n, None

    r = []
    for i, c in enumerate(str(dollars)[::-1]):
        if i and (not (i % 3)):
            r.insert(0, ",")
        r.insert(0, c)
    out = "".join(r)
    if cents:
        out += "." + cents
    return prefix + out


def mapper(
    func: Callable[[list | dict | Any], list | dict | Any],
    ob: Union[list, dict],
) -> list | dict | Any:
    """Map func for list or dict."""
    if isinstance(ob, list):
        result = []
        for i in ob:
            result.append(mapper(func, i))
    elif isinstance(ob, dict):
        result = {}
        for k, v in ob.items():
            value = mapper(func, v) if isinstance(v, (list, dict)) else func(v)
            result[k] = value
    else:
        return func(ob)
    return result


def seconds_to_format_str(
    seconds: int,
    format_str: str = DATETIME_FORMAT_STRING,
    offset: Union[float, int] = 1,
    tzinfo: ZoneInfo = ZoneInfo(
        local_configs.RELATIONAL.TIMEZONE or "Asia/Shanghai",
    ),
) -> str:
    """时间戳装换为对应格式化时间, 需要传秒级时间戳 或者 配合offset转换成秒级."""
    v = datetime.datetime.fromtimestamp(seconds * offset, tz=tzinfo)
    return v.strftime(format_str)


def format_str_to_seconds(
    value: datetime.datetime | str,
    format_str: str = DATETIME_FORMAT_STRING,
    tzinfo: ZoneInfo = ZoneInfo(
        local_configs.RELATIONAL.TIMEZONE or "Asia/Shanghai",
    ),
) -> int:
    """格式化时间转换为对应时区的时间戳."""
    if isinstance(value, datetime.datetime):
        value = value.replace(tzinfo=tzinfo)
    else:
        value = datetime.datetime.strptime(value, format_str).replace(
            tzinfo=tzinfo,
        )
    return int(value.timestamp())


def filter_dict(
    dict_obj: dict,
    callback: Callable[[Hashable, Any], dict],
) -> dict:
    """适用于字典的filter."""
    new_dict = {}
    for key, value in dict_obj.items():
        if callback(key, value):
            new_dict[key] = value
    return new_dict


def flatten_list(element: any) -> list[any]:
    """Iterable 递归展开成一级列表."""
    flat_list = []

    def _flatten_list(e: any) -> None:
        if type(e) in [list, set, tuple]:
            for item in e:
                _flatten_list(item)
        else:
            flat_list.append(e)

    _flatten_list(element)

    return flat_list


def snake2camel(snake: str, start_lower: bool = False) -> str:
    """Converts a snake_case string to camelCase.
    The `start_lower` argument determines whether the first letter in the generated camelcase should
    be lowercase (if `start_lower` is True), or capitalized (if `start_lower` is False).
    """
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return


def camel2snake(camel: str) -> str:
    """Converts a camelCase string to snake_case."""
    snake = re.sub(
        r"([a-zA-Z])([0-9])",
        lambda m: f"{m.group(1)}_{m.group(2)}",
        camel,
    )
    snake = re.sub(
        r"([a-z0-9])([A-Z])",
        lambda m: f"{m.group(1)}_{m.group(2)}",
        snake,
    )
    return snake.lower()
