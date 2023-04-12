import re
import time
import uuid
import random
import string
from typing import Any, Dict, List, Union, Callable, Hashable
from datetime import datetime
from zoneinfo import ZoneInfo

from starlette.requests import Request

from conf.config import local_configs
from common.types import request_id_ctx_var

DATETIME_FORMAT_STRING = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_STRING = "%Y-%m-%d"


def join_params(
    params: Union[dict, list],
    initial=False,
    filter_none: bool = True,
    sep: str = "&",
    exclude_keys: List = None,
):
    """
    参数拼接，用于签名请求
    """
    temp = []

    if type(params) in [dict]:
        if not initial:
            temp.append("{")
        for i, k in enumerate(sorted(params)):
            if exclude_keys and k in exclude_keys:
                continue
            v = params[k]
            if filter_none and v is None:
                continue
            if type(v) in [dict, list]:
                temp.append("{}=".format(k))
                temp.extend(join_params(v))
                if i != len(params) - 1:
                    temp.append(sep)
            else:
                temp.append("{}={}".format(k, v))
                if i != len(params) - 1:
                    temp.append(sep)
        if not initial:
            temp.append("}")
    elif type(params) in [list]:
        temp.append("[")
        for i, v in enumerate(sorted(params)):
            if filter_none and v is None:
                continue
            if type(v) in [dict, list]:
                temp.extend(join_params(v))
                if i != len(params) - 1:
                    temp.append("|")
            else:
                temp.append(str(v))
                if i != len(params) - 1:
                    temp.append("|")
        temp.append("]")

    return temp


def generate_random_string(
    length: int, all_digits: bool = False, excludes: List = None
):
    """
    生成任意长度字符串
    """
    if excludes is None:
        excludes = []
    if all_digits:
        all_char = string.digits
    else:
        all_char = string.ascii_letters + string.digits
    if excludes:
        for char in excludes:
            all_char.replace(char, "")
    return "".join(random.sample(all_char, length))


def get_client_ip(request: Request):
    """
    获取客户端真实ip
    :param request:
    :return:
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


def datetime_now():
    # 返回带有时区信息的时间
    return datetime.now(
        tz=ZoneInfo(local_configs.RELATIONAL.TIMEZONE or "Asia/Shanghai")
    )


def commify(n: Union[int, float]):
    """
    Add commas to an integer `n`.
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
        >>>
    """
    if n is None:
        return None

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


def mapper(func, ob: Union[List, Dict]):
    """
    map func for list or dict
    """
    if isinstance(ob, list):
        for i in ob:
            mapper(func, i)
    elif isinstance(ob, dict):
        for k, v in ob.items():
            if isinstance(v, dict):
                mapper(func, v)
            else:
                ob[k] = func(v)
    else:
        func(ob)


def merge_dict(dict1: dict, dict2: dict = None, reverse: bool = False):
    """
    合并字典
    """
    try:
        if not dict2:
            merged = dict1
        else:
            merged = {**dict1, **dict2}
    except (AttributeError, ValueError) as e:
        raise TypeError("original and updates must be a dictionary: %s" % e)

    if not reverse:
        return merged
    else:
        return {v: k for k, v in merged.items()}


def seconds_to_format_str(
    seconds,
    format_str: str = DATETIME_FORMAT_STRING,
    offset: Union[float, int] = 1,
):
    """时间戳装换为格式化时间"""
    return time.strftime(format_str, time.localtime(seconds * offset))


def format_str_to_seconds(value, format_str: str = DATETIME_FORMAT_STRING):
    """格式化时间转换为时间戳"""
    if isinstance(value, datetime.datetime):
        value = datetime.strftime(value, format_str)
    value = time.strptime(value, format_str)
    return int(time.mktime(value))


def filter_dict(dict_obj: dict, callback: Callable[[Hashable, Any], dict]):
    """
    适用于字典的filter
    """
    new_dict = {}
    for key, value in dict_obj.items():
        if callback(key, value):
            new_dict[key] = value
    return new_dict


def flatten_list(element):
    """
    Iterable 递归展开成一级列表
    """
    flat_list = []

    def _flatten_list(e):
        if type(e) in [list, set, tuple]:
            for item in e:
                _flatten_list(item)
        else:
            flat_list.append(e)

    _flatten_list(element)

    return flat_list


def snake2camel(snake: str, start_lower: bool = False) -> str:
    """
    Converts a snake_case string to camelCase.
    The `start_lower` argument determines whether the first letter in the generated camelcase should
    be lowercase (if `start_lower` is True), or capitalized (if `start_lower` is False).
    """
    camel = snake.title()
    camel = re.sub("([0-9A-Za-z])_(?=[0-9A-Z])", lambda m: m.group(1), camel)
    if start_lower:
        camel = re.sub("(^_*[A-Z])", lambda m: m.group(1).lower(), camel)
    return


def camel2snake(camel: str) -> str:
    """
    Converts a camelCase string to snake_case.
    """
    snake = re.sub(
        r"([a-zA-Z])([0-9])", lambda m: f"{m.group(1)}_{m.group(2)}", camel
    )
    snake = re.sub(
        r"([a-z0-9])([A-Z])", lambda m: f"{m.group(1)}_{m.group(2)}", snake
    )
    return snake.lower()


def get_or_set_request_id():
    request_id = request_id_ctx_var.get()
    if not request_id:
        request_id = str(uuid.uuid4())
        request_id_ctx_var.set(request_id)
    return request_id


def get_request_id():
    return request_id_ctx_var.get()


def reset_request_id():
    request_id_ctx_var.set(None)
