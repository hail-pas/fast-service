import uuid

from pydantic import Field
from tortoise.contrib.pydantic import pydantic_model_creator

from common.pydantic import optional
from storages.relational.models import Resource

ResourceList = pydantic_model_creator(
    Resource,
    name="SystemResourceList",
    exclude=[
        "parent",
        "rely_on",
        "permissions",
        "systems",
        "children",
        "relied_nodes",
        "roles",
    ],
)


ResourceDetail = pydantic_model_creator(Resource, name="SystemResourceDetail")


class ResourceCreate(
    pydantic_model_creator(
        Resource,
        name="SystemResourceCreate",
        exclude=["deleted_at"],
        exclude_readonly=True,
    ),
):
    permissions: list[uuid.UUID] = Field([], description="权限id列表")


@optional
class ResourceUpdate(ResourceCreate):
    ...


ResourceLevelTreeBaseNode = pydantic_model_creator(
    Resource,
    name="ResourceLevelTreeBaseNode",
    exclude=[
        "parent",
        "rely_on",
        "permissions",
        "systems",
        "children",
        "relied_nodes",
        "roles",
    ],
)


class ResourceLevelTreeNode(ResourceLevelTreeBaseNode):
    children: list["ResourceLevelTreeNode"] = Field([], description="子节点")
