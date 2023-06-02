from pydantic import Field
from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models import System
from storages.relational.pydantic.role import RoleList

SystemList = pydantic_model_creator(
    System,
    name="SystemList",
    exclude=[
        "resources",
        "roles",
    ],
)

SystemDetail = pydantic_model_creator(
    System,
    name="SystemDetail",
    exclude=[
        "resources",
        "roles",
    ],
)


class SystemListWithRoles(
    pydantic_model_creator(
        System,
        name="SystemListWithRoles",
        exclude=[
            "resources",
            # "roles",
        ],
    ),
):
    roles: list[RoleList] = Field(..., description="角色列表")


SystemCreate = pydantic_model_creator(
    System,
    name="SystemCreate",
    exclude=["deleted_at"],
    exclude_readonly=True,
)


@optional
class SystemUpdate(SystemCreate):
    pass
