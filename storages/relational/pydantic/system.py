from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models import System

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

SystemCreate = pydantic_model_creator(
    System, name="SystemCreate", exclude=["deleted_at"], exclude_readonly=True
)


@optional
class SystemUpdate(SystemCreate):
    pass
