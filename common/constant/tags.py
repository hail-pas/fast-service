from common.types import StrEnumMore


class TagsEnum(StrEnumMore):
    """Tags"""

    root = ("Root", "根目录")
    authorization = ("Authorization", "授权相关")
    account = ("Account", "账户信息管理")
    role = ("Role", "角色管理")
    system = ("System", "系统管理")
    permission = ("Permission", "权限管理")
    resource = ("Resource", "资源管理")
    # >> 新增tag
    other = ("Other", "其他")


class OuterAppTagsEnum(StrEnumMore):
    """Outer Tags"""

    ping = ("Ping", "Ping")
    # >> 新增tag
