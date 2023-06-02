import uuid
from datetime import datetime

from pydantic import Field, BaseModel, validator
from tortoise.contrib.pydantic import pydantic_model_creator

from common.encrypt import PasswordUtil
from common.pydantic import optional
from storages.relational.models import Account
from storages.relational.pydantic.role import RoleList
from storages.relational.pydantic.system import SystemListWithRoles

# from storages.relational.pydantic.resource import ResourceLevelTreeNode

AccountList = pydantic_model_creator(
    Account,
    name="AccountList",
    exclude=[
        "password",
        "roles",
    ],
)


class AccountDetail(
    pydantic_model_creator(
        Account,
        name="AccountDetail",
        exclude=["password"],
    ),
):
    roles: list[RoleList] = Field([], description="角色列表")


class AccountDetailWithResource(AccountDetail):
    systems: list[SystemListWithRoles] = Field([], description="系统列表")
    # resources: List[ResourceLevelTreeNode] = Field([], description="资源列表")


class AccountCreate(
    pydantic_model_creator(
        Account,
        name="AccountCreate",
        exclude=["deleted_at", "status", "last_login_at"],
        exclude_readonly=True,
    ),
):
    roles: list[uuid.UUID] = Field(..., description="角色id列表")

    @validator("password")
    def gen_password_hash(cls, v):
        return PasswordUtil.get_password_hash(v)


@optional
class AccountUpdate(
    pydantic_model_creator(
        Account,
        name="AccountUpdate",
        exclude=["deleted_at", "last_login_at"],
        exclude_readonly=True,
    ),
):
    pass


class AuthData(BaseModel):
    token_type: str
    access_token: str
    expired_at: datetime
    account: AccountDetailWithResource

    class Config:
        orm_mode = True
