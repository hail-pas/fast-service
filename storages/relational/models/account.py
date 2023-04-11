from typing import Optional

from tortoise import fields

from storages import enums
from conf.config import local_configs
from common.utils import datetime_now
from storages.relational.models.base import BaseModel, UUIDPrimaryKeyModel


class Account(BaseModel):
    username = fields.CharField(max_length=32, description="用户名", index=True)
    nickname = fields.CharField(max_length=48, description="昵称")
    password = fields.CharField(max_length=128, description="密码")
    last_login_at = fields.DatetimeField(null=True, description="最近一次登录时间")
    remark = fields.CharField(max_length=256, default="", description="备注")
    avatar_uri = fields.CharField(max_length=256, default="", description="头像")
    status = fields.CharEnumField(
        max_length=16,
        enum_type=enums.StatusEnum,
        description="状态",
        default=enums.StatusEnum.enable,
    )

    # reversed relations
    roles: fields.ManyToManyRelation["Role"]

    def __str__(self):
        return f"{self.username}-{self.phone}"

    def status_display(self) -> str:
        """
        状态显示
        """
        return self._meta.fields_map.get("status").enum_type.dict.get(
            self.status.value
        )

    def days_from_last_login(self) -> Optional[int]:
        """
        距上一次登录天数
        :return:
        """
        if not self.last_login_at:
            return None
        return (datetime_now() - self.last_login_at).days

    def avatar_url(self) -> str:
        if not self.avatar_uri:
            return ""
        return f"{local_configs.OSS.ENDPOINT}{self.avatar}"

    class Meta:
        table_description = "用户"
        ordering = ["-created_at"]
        unique_together = (("username", "deleted_at"),)

    class PydanticMeta:
        computed = ("days_from_last_login", "status_display", "avatar_url")


class Permission(UUIDPrimaryKeyModel):
    code = fields.CharField(max_length=64, description="权限码", unique=True)
    label = fields.CharField(max_length=128, description="权限名称")
    type = fields.CharEnumField(
        max_length=16,
        enum_type=enums.PermissionTypeEnum,
        description="权限类型",
        default=enums.PermissionTypeEnum.api,
    )
    is_deprecated = fields.BooleanField(default=False, description="是否废弃")

    # reversed relations
    roles: fields.ManyToManyRelation["Role"]

    class Meta:
        table_description = "权限"


class System(BaseModel):
    code = fields.CharField(max_length=64, description="系统唯一标识", unique=True)
    label = fields.CharField(max_length=128, description="系统名称")

    # reversed relations
    roles: fields.ManyToManyRelation["Role"]
    resources: fields.ManyToManyRelation["Resource"]

    class Meta:
        table_description = "系统"


class Resource(BaseModel):
    parent = fields.ForeignKeyField(
        "master.Resource", related_name="children", null=True, description="父级"
    )
    code = fields.CharField(
        max_length=32, description="资源编码{parent}:{current}", index=True
    )
    label = fields.CharField(max_length=64, description="资源名称", index=True)
    front_route = fields.CharField(
        max_length=128, description="前端路由", null=True, blank=True
    )
    type = fields.CharField(
        max_length=16,
        enum_type=enums.SystemResourceTypeEnum,
        description="资源类型",
    )
    rely_on = fields.ForeignKeyField(
        "master.Resource",
        related_name="relied_nodes",
        null=True,
        desscription="关联依赖",
    )
    order_num = fields.IntField(default=1, description="排列序号")
    enabled = fields.BooleanField(default=True, description="当前分组是否可用")
    assignable = fields.BooleanField(default=True, description="配置时是否可分配")
    permissions: fields.ManyToManyRelation[
        Permission
    ] = fields.ManyToManyField("master.Permission", related_name="resources")
    systems: fields.ManyToManyRelation["System"] = fields.ManyToManyField(
        "master.System", related_name="resources"
    )

    # reversed relations
    roles: fields.ManyToManyRelation["Role"]

    children: fields.ReverseRelation["Resource"]

    class Meta:
        table_description = "系统资源"
        ordering = ["order_num"]
        unique_together = (("code", "parent"),)


class Role(BaseModel):
    code = fields.CharField(max_length=32, description="角色编码", index=True)
    label = fields.CharField(max_length=64, description="角色名称", index=True)
    accounts: fields.ManyToManyRelation[Account] = fields.ManyToManyField(
        "master.Account", related_name="roles"
    )
    permissions: fields.ManyToManyRelation[
        Permission
    ] = fields.ManyToManyField("master.Permission", related_name="roles")
    resources: fields.ManyToManyRelation[Resource] = fields.ManyToManyField(
        "master.Resource", related_name="roles"
    )
    systems: fields.ManyToManyRelation["System"] = fields.ManyToManyField(
        "master.System", related_name="roles"
    )

    class Meta:
        table_description = "角色"
        ordering = ["-created_at"]
