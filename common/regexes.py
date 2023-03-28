import re
import socket
import string
import ipaddress
from typing import Tuple, Union

from _socket import gaierror

PHONE_REGEX_CN = re.compile(r"^1[3-9]\d{9}$")

PHONE_REGEX_GLOBAL = re.compile(r"^\+[1-9]\d{1,14}$")


def only_alphabetic_numeric(value: str) -> bool:
    if value is None:
        return False
    options = string.ascii_letters + string.digits + "_"
    if not all([i in options for i in value]):
        return False
    return True


def validate_ip_or_host(value: Union[int, str]) -> Tuple[bool, str]:
    try:
        return True, str(ipaddress.ip_address(value))
    except ValueError:
        if isinstance(value, int):
            return False, "不支持数字IP"
        try:
            socket.gethostbyname(value)
            return True, value
        except gaierror as e:
            return False, f"获取HOST失败: {e}"
