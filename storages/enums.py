"""
全部的Enum类型
"""
import sys
import inspect
from typing import Optional

from common.types import IntEnumMore, StrEnumMore


class SystemResourceTypeEnum(StrEnumMore):
    """
    系统资源
    """

    menu = ("menu", "菜单")
    button = ("button", "按钮")
    api = ("api", "接口")


class PermissionTypeEnum(StrEnumMore):
    """
    权限类型
    """

    api = ("api", "API")


class StatusEnum(StrEnumMore):
    """启用状态"""

    enable = ("enable", "启用")
    disable = ("disable", "禁用")


class ProtocolEnum(StrEnumMore):
    """协议"""

    https = ("https", "https")
    http = ("http", "http")
    rpc = ("rpc", "rpc")


class RespFormatEnum(StrEnumMore):
    list_ = ("list", "列表")
    json_ = ("json", "JSON")


class IOrderEnum(StrEnumMore):
    ascendent = ("ascendent", "升序")
    descendent = ("descendent", "降序")


# ==================================================
# 在该行上面新增 Enum 类
# ==================================================
# [("name", Enum)]
__enum_set__ = list(
    filter(
        lambda cls_name_and_cls: True
        if issubclass(cls_name_and_cls[1], (StrEnumMore, IntEnumMore))
        and cls_name_and_cls[1] not in [StrEnumMore, IntEnumMore]
        else False,
        inspect.getmembers(sys.modules[__name__], inspect.isclass),
    )
)

__enum_choices__ = list(
    map(
        lambda cls_name_and_cls: (
            cls_name_and_cls[0],
            cls_name_and_cls[1].__doc__.strip(),
        ),
        __enum_set__,
    )
)


def get_enum_content(
    enum_name: Optional[str] = None, is_reversed: bool = False
):
    enum_content = {}
    enum_list = []
    if enum_name:
        try:
            enum_cls = getattr(sys.modules[__name__], enum_name)
            enum_list.append((enum_name, enum_cls))
        except (AttributeError, NotImplementedError):
            pass
    else:
        enum_list = __enum_set__

    for name, cls in enum_list:
        # if format_ == EnumInfoResponseFormats.list_.value:
        #     enum_content[name] = cls.choices
        # else:
        if is_reversed:
            enum_content[name] = {v: k for k, v in cls.dict.items()}
        else:
            enum_content[name] = cls.dict

    return enum_content
