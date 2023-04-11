from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models import Permission

PermissionList = pydantic_model_creator(
    Permission,
    name="PermissionList",
    exclude=[
        "resources",
        "roles",
    ],
)

PermissionDetail = pydantic_model_creator(
    Permission,
    name="PermissionDetail",
    exclude=[
        "resources",
        "roles",
    ],
)
PermissionCreate = pydantic_model_creator(
    Permission,
    name="PermissionCreate",
    exclude=["deleted_at"],
    exclude_readonly=True,
)


@optional
class PermissionUpdate(PermissionCreate):
    pass
