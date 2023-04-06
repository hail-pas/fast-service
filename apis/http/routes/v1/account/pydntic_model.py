import uuid
from typing import List, Optional
from dataclasses import dataclass

from fastapi import Query
from pydantic import Field
from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models.account import (
    Role,
    System,
    Account,
    Resource,
    Permission,
)

RoleDetail = pydantic_model_creator(
    Role, name="RoleDetail", exclude=["accounts"]
)
RoleList = pydantic_model_creator(
    Role, name="RoleList", exclude=["accounts", "role"]
)
RoleCreate = pydantic_model_creator(
    Role,
    name="RoleCreate",
    exclude=["accounts", "deleted_at"],
    exclude_readonly=True,
)


class AccountDetail(
    pydantic_model_creator(Account, name="AccountDetail", exclude=["password"])
):
    roles: List[RoleList] = Field(..., description="角色列表")


AccountList = pydantic_model_creator(
    Account, name="AccountList", exclude=["password"]
)


class AccountCreate(
    pydantic_model_creator(
        Account,
        name="AccountCreate",
        exclude=["deleted_at", "status", "last_login_at"],
        exclude_readonly=True,
    )
):
    roles: List[uuid.UUID] = Field(..., description="角色id列表")


AccountUpdate = pydantic_model_creator(
    Account,
    name="AccountUpdate",
    exclude=["deleted_at", "last_login_at"],
    exclude_readonly=True,
)


SystemDetail = pydantic_model_creator(System, name="SystemDetail")
SystemCreate = pydantic_model_creator(
    System, name="SystemCreate", exclude=["deleted_at"], exclude_readonly=True
)

PermissionDetail = pydantic_model_creator(Permission, name="PermissionDetail")
PermissionCreate = pydantic_model_creator(
    Permission,
    name="PermissionCreate",
    exclude=["deleted_at"],
    exclude_readonly=True,
)

SystemResourceDetail = pydantic_model_creator(
    Resource, name="SystemResourceDetail"
)


class SystemResourceCreate(
    pydantic_model_creator(
        Resource,
        name="SystemResourceCreate",
        exclude=["deleted_at"],
        exclude_readonly=True,
    )
):
    parent: Optional[str] = Field(None, description="父级资源id")
    rely_on: Optional[str] = Field(None, description="依赖资源id")
    permissions: List[uuid.UUID] = Field(None, description="权限id列表")


@optional
class SystemResourceUpdate(SystemResourceCreate):
    ...


@dataclass
class SystemResourceFilterSchema:
    code: str = Query(None, description="资源名称")
    label: str = Query(None, description="系统id")
    parent: str = Query(None, description="父级资源id")
    rely_on: str = Query(None, description="依赖资源id")

    def __post_init__(self, *args, **kwargs):
        # validate or add custom field
        self.extra_args = []
        self.extra_kwargs = {}

    # def __post_init_post_parse__(self):
    #     pass
