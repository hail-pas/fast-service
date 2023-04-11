from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models import Role

RoleList = pydantic_model_creator(
    Role,
    name="RoleList",
    exclude=["accounts", "permissions", "resources", "systems"],
)

RoleDetail = pydantic_model_creator(
    Role,
    name="RoleDetail",
    exclude=["accounts", "systems", "resources", "permissions"],
)

RoleCreate = pydantic_model_creator(
    Role,
    name="RoleCreate",
    exclude=["accounts", "deleted_at"],
    exclude_readonly=True,
)


@optional
class RoleUpdate(RoleCreate):
    ...
